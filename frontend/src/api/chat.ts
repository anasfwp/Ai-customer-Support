import { apiClient } from './client';
import type { ChatHistoryItem, ChatQueryResponse } from '../types';

export const chatApi = {
  /**
   * Ask a question using the RAG pipeline.
   */
  query: async (question: string, sessionId?: string): Promise<ChatQueryResponse> => {
    const response = await apiClient.post<ChatQueryResponse>('/api/v1/chat/query', {
      question,
      session_id: sessionId ?? null,
    });
    return response.data;
  },

  /**
   * Get chat history for the current user.
   */
  history: async (limit = 50): Promise<ChatHistoryItem[]> => {
    const response = await apiClient.get<ChatHistoryItem[]>('/api/v1/chat/history', {
      params: { limit },
    });
    return response.data;
  },
};