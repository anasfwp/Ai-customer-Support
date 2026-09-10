import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import ChatMessage from './ChatMessage';
import type { Message } from '../../types';

interface ChatWindowProps {
  messages: Message[];
  onFeedback: (messageId: string, value: 'helpful' | 'unhelpful') => void;
  onSuggestionClick?: (text: string) => void;
}

const suggestions = [
  'What is the refund policy?',
  'How do I reset my password?',
  'What are the business hours?',
  'Do you ship internationally?',
];

export default function ChatWindow({ messages, onFeedback, onSuggestionClick }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the newest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mx-auto max-w-2xl text-center"
        >
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20">
            <Sparkles className="h-8 w-8 text-white" />
          </div>

          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            How can I help you today?
          </h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-slate-500 dark:text-slate-400">
            Ask anything about your uploaded documents. I&apos;ll answer with citations from your
            knowledge base.
          </p>

          <div className="mt-8 grid gap-3 sm:grid-cols-2">
            {suggestions.map((text, i) => (
              <motion.button
                key={text}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 + i * 0.05 }}
                onClick={() => onSuggestionClick?.(text)}
                className="rounded-xl border border-slate-200 bg-white p-4 text-left text-sm text-slate-700 transition hover:border-indigo-300 hover:bg-indigo-50/50 hover:shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-indigo-700 dark:hover:bg-indigo-950/30"
              >
                {text}
              </motion.button>
            ))}
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-6 sm:px-6">
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} onFeedback={onFeedback} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}