import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { authApi } from '../api/auth';
import { sessionNotice, tokenStorage } from '../api/client';

interface AuthUser {
  email: string;
  tenantId: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, companyName: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Decode a JWT payload without verifying the signature.
 * Used only to read the email + tenant_id for display purposes.
 */
function decodeJwt(token: string): Record<string, unknown> | null {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

function userFromToken(token: string | null): AuthUser | null {
  if (!token) return null;
  const payload = decodeJwt(token);
  if (!payload) return null;

  const email = typeof payload.sub === 'string' ? payload.sub : '';
  const tenantId = typeof payload.tenant_id === 'string' ? payload.tenant_id : '';

  if (!email || !tenantId) return null;

  // Treat an expired token as signed out instead of showing the app until the
  // first API call fails with a 401.
  if (typeof payload.exp === 'number' && payload.exp * 1000 <= Date.now()) {
    tokenStorage.clear();
    sessionNotice.flagExpired();
    return null;
  }
  return { email, tenantId };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => userFromToken(tokenStorage.get()));
  const [isLoading, setIsLoading] = useState(false);

  // Keep user state in sync if token changes in another tab.
  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key === 'access_token') {
        setUser(userFromToken(event.newValue));
      }
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await authApi.login(email, password);
      tokenStorage.set(response.access_token);
      setUser(userFromToken(response.access_token));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (email: string, password: string, companyName: string) => {
    setIsLoading(true);
    try {
      const response = await authApi.register({
        email,
        password,
        company_name: companyName,
      });
      tokenStorage.set(response.access_token);
      setUser(userFromToken(response.access_token));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      register,
      logout,
    }),
    [user, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}