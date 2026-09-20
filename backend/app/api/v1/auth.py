from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.models.user import User
from app.db.models.tenant import Tenant
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.limiter import limiter
from app.config import settings
from pydantic import BaseModel, EmailStr, field_validator

router = APIRouter()

MIN_PASSWORD_LENGTH = 8

# Verified against when the email doesn't exist, so an unknown account costs
# the same bcrypt time as a wrong password (no timing-based user enumeration).
_DUMMY_HASH = get_password_hash("timing-equalizer")


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
        return v

    @field_validator("company_name")
    @classmethod
    def company_name_not_blank(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Company name cannot be empty")
        return v


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create tenant
    tenant = Tenant(name=user_data.company_name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        tenant_id=tenant.id,
        is_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    access_token = create_access_token(
        data={"sub": user.email, "tenant_id": tenant.id}
    )

    return {
        "user_id": user.id,
        "tenant_id": tenant.id,
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    password_ok = verify_password(
        form_data.password, user.hashed_password if user else _DUMMY_HASH
    )
    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = create_access_token(
        data={"sub": user.email, "tenant_id": user.tenant_id}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
