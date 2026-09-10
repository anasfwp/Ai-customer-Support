import { apiClient } from './client';
import type { FeedbackRequest, FeedbackStats } from '../types';

export const feedbackApi = {
  /**
   * Submit feedback for a chat response.
   */
  submit: async (data: FeedbackRequest): Promise<{ message: string; feedback_id: string }> => {
    const response = await apiClient.post('/api/v1/feedback/', data);
    return response.data;
  },

  /**
   * Get feedback statistics.
   */
  stats: async (): Promise<FeedbackStats> => {
    const response = await apiClient.get<FeedbackStats>('/api/v1/feedback/stats');
    return response.data;
  },
};