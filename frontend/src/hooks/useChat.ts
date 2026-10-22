import { useCallback, useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { chatApi } from '../api/chat';
import { errorMessage } from '../api/client';
import { feedbackApi } from '../api/feedback';
import type { ChatHistoryItem, Message } from '../types';

const HISTORY_KEY = ['chat', 'history'] as const;

/**
 * Flatten stored chat history into a user+assistant message list.
 */
function historyToMessages(items: ChatHistoryItem[]): Message[] {
  return [...items]
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .flatMap((item): Message[] => {
      const confidence = item.confidence ? parseFloat(item.confidence) : undefined;
      return [
        {
          id: `${item.id}-q`,
          role: 'user',
          content: item.question,
          citations: [],
          createdAt: item.created_at,
        },
        {
          id: `${item.id}-a`,
          role: 'assistant',
          content: item.answer,
          citations: item.citations ?? [],
          confidence,
          fallback: item.fallback,
          chatLogId: item.id,
          sessionId: item.session_id,
          createdAt: item.created_at,
        },
      ];
    });
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const hydratedRef = useRef(false);
  const queryClient = useQueryClient();

  const historyQuery = useQuery({
    queryKey: [...HISTORY_KEY],
    queryFn: () => chatApi.history(50),
    staleTime: 30_000,
  });

  // Load history into the message list exactly once.
  useEffect(() => {
    if (historyQuery.data && !hydratedRef.current) {
      hydratedRef.current = true;
      if (historyQuery.data.length > 0) {
        setMessages(historyToMessages(historyQuery.data));
        setSessionId(historyQuery.data[historyQuery.data.length - 1].session_id);
      }
    }
  }, [historyQuery.data]);

  const sendMutation = useMutation({
    mutationFn: ({ question, pendingId }: { question: string; pendingId: string }) =>
      chatApi.stream(question, sessionId, (answer) =>
        setMessages((prev) =>
          prev.map((m) => (m.id === pendingId ? { ...m, content: answer } : m)),
        ),
      ),
    onMutate: ({ question, pendingId }) => {
      const now = new Date().toISOString();
      const userMsg: Message = {
        id: `u-${Date.now()}`,
        role: 'user',
        content: question,
        citations: [],
        createdAt: now,
      };
      const pendingMsg: Message = {
        id: pendingId,
        role: 'assistant',
        content: '',
        citations: [],
        pending: true,
        createdAt: now,
      };
      setMessages((prev) => [...prev, userMsg, pendingMsg]);
      return { pendingId: pendingMsg.id };
    },
    onSuccess: (data, _question, context) => {
      setSessionId(data.session_id);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === context?.pendingId
            ? {
                ...m,
                pending: false,
                content: data.answer,
                citations: data.citations ?? [],
                confidence: data.confidence,
                fallback: data.fallback,
                chatLogId: data.chat_log_id ?? data.id,
                sessionId: data.session_id,
                searchQuery: data.search_query,
              }
            : m,
        ),
      );
      queryClient.invalidateQueries({ queryKey: [...HISTORY_KEY] });
    },
    onError: (error, _question, context) => {
      setMessages((prev) => prev.filter((m) => m.id !== context?.pendingId));
      toast.error(errorMessage(error, 'Failed to get an answer. Please try again.'));
    },
  });

  const newChat = useCallback(() => {
    setMessages([]);
    setSessionId(undefined);
  }, []);

  const setFeedback = useCallback(
    (messageId: string, value: 'helpful' | 'unhelpful') => {
      // Optimistic UI update
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, feedback: value } : m)),
      );

      // Find the message to get the chat_log_id
      const message = messages.find((m) => m.id === messageId);
      if (message?.chatLogId) {
        feedbackApi
          .submit({
            chat_log_id: message.chatLogId,
            helpful: value === 'helpful',
          })
          .catch(() => {
            toast.error('Failed to save feedback');
          });
      }
    },
    [messages],
  );

  return {
    messages,
    sessionId,
    isLoadingHistory: historyQuery.isLoading,
    isSending: sendMutation.isPending,
    send: (question: string) => sendMutation.mutate({ question, pendingId: `a-${Date.now()}` }),
    newChat,
    setFeedback,
  };
}