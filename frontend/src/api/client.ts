import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';

const TOKEN_KEY = 'access_token';
const SESSION_EXPIRED_KEY = 'session_expired';

/**
 * In development, Vite proxies /api to http://localhost:8000.
 * In production, set VITE_API_BASE_URL to the backend URL.
 */
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120_000,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT to every request
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Global error handling: auto-logout on 401
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && !error.config?.url?.includes('/auth/login')) {
      handleUnauthorized();
    }
    return Promise.reject(error);
  },
);

/**
 * Sign out and send the user to /login. Shared with fetch-based calls (streaming) that bypass axios.
 */
export function handleUnauthorized() {
  if (localStorage.getItem(TOKEN_KEY)) sessionNotice.flagExpired();
  localStorage.removeItem(TOKEN_KEY);
  if (!window.location.pathname.startsWith('/login')) {
    window.location.href = '/login';
  }
}

/**
 * Extract a human-readable message from an axios error.
 */
export function errorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 429) {
      return 'Too many attempts. Please wait a minute and try again.';
    }
    if (!error.response) {
      return error.code === 'ECONNABORTED'
        ? 'The server took too long to respond. Please try again.'
        : 'Cannot reach the server. Check your connection and try again.';
    }
    const data = error.response.data as Record<string, unknown> | undefined;
    if (typeof data?.detail === 'string') return data.detail;
    if (typeof data?.message === 'string') return data.message;
    if (Array.isArray(data?.detail) && data.detail.length > 0) {
      const first = data.detail[0] as Record<string, unknown>;
      if (typeof first?.msg === 'string') return first.msg;
    }
    return error.message || fallback;
  }
  return error instanceof Error ? error.message : fallback;
}

/**
 * One-shot flag so the login page can explain why the user was signed out.
 * sessionStorage can throw (private mode / blocked storage), so never let it
 * break the auth flow.
 */
export const sessionNotice = {
  flagExpired: () => {
    try {
      sessionStorage.setItem(SESSION_EXPIRED_KEY, '1');
    } catch {
      /* ignore */
    }
  },
  consumeExpired: (): boolean => {
    try {
      const flagged = sessionStorage.getItem(SESSION_EXPIRED_KEY) === '1';
      sessionStorage.removeItem(SESSION_EXPIRED_KEY);
      return flagged;
    } catch {
      return false;
    }
  },
};

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};