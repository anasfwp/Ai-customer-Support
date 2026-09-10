import { apiClient } from './client';
import type { LoginResponse, RegisterRequest, RegisterResponse } from '../types';

export const authApi = {
  /**
   * Register a new user + tenant.
   */
  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    const response = await apiClient.post<RegisterResponse>('/api/v1/auth/register', data);
    return response.data;
  },

  /**
   * Login with email and password.
   * Backend uses OAuth2PasswordRequestForm (form-data).
   */
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
};