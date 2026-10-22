import { API_BASE_URL, apiClient, handleUnauthorized, tokenStorage } from './client';
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
   * Ask a question and receive the answer as it is generated (server-sent events).
   * `onText` gets the full answer so far after each token.
   */
  stream: async (
    question: string,
    sessionId: string | undefined,
    onText: (answer: string) => void,
  ): Promise<ChatQueryResponse> => {
    const token = tokenStorage.get();
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ question, session_id: sessionId ?? null }),
    });
    if (response.status === 401) handleUnauthorized();
    if (response.status === 429) throw new Error('Too many attempts. Please wait a minute and try again.');
    if (!response.ok || !response.body) {
      const data = await response.json().catch(() => ({}));
      throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed to get an answer. Please try again.');
    }

    const result = { answer: '' } as ChatQueryResponse;
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() ?? '';
      for (const raw of events) {
        const event = raw.match(/^event: (.*)$/m)?.[1];
        const data = JSON.parse(raw.match(/^data: (.*)$/m)?.[1] ?? '{}');
        if (event === 'meta') Object.assign(result, data);
        else if (event === 'token') onText((result.answer += data.text));
        else if (event === 'done') result.chat_log_id = data.chat_log_id;
        else if (event === 'error') throw new Error(data.detail);
      }
    }
    if (!result.chat_log_id) throw new Error('The answer was cut off. Please try again.');
    return result;
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