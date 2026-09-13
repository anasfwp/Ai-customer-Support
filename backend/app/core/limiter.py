from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared rate limiter instance (per-client-IP). Defined in its own module
# so both main.py (registration/exception handler) and individual routers
# (per-route limits) can import it without a circular import.
limiter = Limiter(key_func=get_remote_address)
