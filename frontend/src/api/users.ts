import { apiClient } from './client';
import type { AddMemberRequest, TeamMember } from '../types';

export const usersApi = {
  /**
   * Everyone in the current user's company.
   */
  list: async (): Promise<TeamMember[]> => {
    const response = await apiClient.get<TeamMember[]>('/api/v1/users/');
    return response.data;
  },

  /**
   * Create an account in the admin's company (admin only).
   */
  add: async (data: AddMemberRequest): Promise<TeamMember> => {
    const response = await apiClient.post<TeamMember>('/api/v1/users/', data);
    return response.data;
  },
};
