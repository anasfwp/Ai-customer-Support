import { apiClient } from './client';
import type { UnansweredQuestion, UsageStats } from '../types';

export const analyticsApi = {
  /**
   * Get usage statistics.
   */
  usage: async (): Promise<UsageStats> => {
    const response = await apiClient.get<UsageStats>('/api/v1/analytics/usage');
    return response.data;
  },

  /**
   * Get questions that triggered the fallback response.
   */
  unanswered: async (): Promise<UnansweredQuestion[]> => {
    const response = await apiClient.get<UnansweredQuestion[]>('/api/v1/analytics/unanswered');
    return response.data;
  },
};