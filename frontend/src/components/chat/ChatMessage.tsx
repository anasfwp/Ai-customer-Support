import { useState } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { AlertTriangle, Bot, Copy } from 'lucide-react';
import toast from 'react-hot-toast';
import CitationBadge from './CitationBadge';
import CitationModal from './CitationModal';
import FeedbackButtons from './FeedbackButtons';
import TypingIndicator from './TypingIndicator';
import type { Citation, Message } from '../../types';
import { cn } from '../../utils/cn';

interface ChatMessageProps {
  message: Message;
  onFeedback: (messageId: string, value: 'helpful' | 'unhelpful') => void;
}

function ConfidenceIndicator({ confidence }: { confidence: number }) {
  const { label, dot } =
    confidence >= 0.75
      ? { label: 'High confidence', dot: 'bg-emerald-500' }
      : confidence >= 0.5
        ? { label: 'Medium confidence', dot: 'bg-amber-500' }
        : { label: 'Low confidence', dot: 'bg-red-500' };

  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-slate-400">
      <span className={cn('h-2 w-2 rounded-full', dot)} />
      {label} · {Math.round(confidence * 100)}%
    </span>
  );
}

export default function ChatMessage({ message, onFeedback }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const copyAnswer = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      toast.success('Copied to clipboard');
    } catch {
      toast.error('Could not copy answer');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className={cn('flex gap-3', isUser && 'flex-row-reverse')}
    >
      {/* Avatar */}
      {isUser ? (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-xs font-bold text-white">
          You
        </div>
      ) : (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-900 dark:bg-indigo-500">
          <Bot className="h-[18px] w-[18px] text-white" />
        </div>
      )}

      <div className={cn('min-w-0 max-w-[85%] sm:max-w-[75%]', isUser && 'flex flex-col items-end')}>
        {isUser ? (
          <div className="rounded-2xl rounded-tr-sm bg-indigo-600 px-4 py-3 text-sm leading-6 text-white shadow-sm shadow-indigo-600/20">
            {message.content}
          </div>
        ) : (
          <div
            className={cn(
              'rounded-2xl rounded-tl-sm border px-4 py-3 shadow-sm',
              message.fallback
                ? 'border-amber-200 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/40'
                : 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900',
            )}
          >
            {message.fallback && (
              <div className="mb-2 flex items-center gap-2 text-xs font-medium text-amber-700 dark:text-amber-400">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                Not found in your documents — answered from general knowledge
              </div>
            )}

            {/* Content */}
            {message.pending && !message.content ? (
              <TypingIndicator />
            ) : (
              <div className="markdown-body text-sm text-slate-700 dark:text-slate-200">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            )}

            {/* Citations */}
            {!message.pending && message.citations.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {message.citations.map((c, i) => (
                  <CitationBadge
                    key={`${c.document_id}-${i}`}
                    citation={c}
                    onClick={() => setActiveCitation(c)}
                  />
                ))}
              </div>
            )}

            {/* Footer: confidence + actions */}
            {!message.pending && (
              <div className="mt-3 flex items-center gap-3 border-t border-slate-100 pt-2.5 dark:border-slate-800">
                {message.confidence != null && (
                  <ConfidenceIndicator confidence={message.confidence} />
                )}
                <div className="ml-auto flex items-center gap-1">
                  <button
                    onClick={copyAnswer}
                    aria-label="Copy answer"
                    className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                  <FeedbackButtons message={message} onFeedback={onFeedback} />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <CitationModal citation={activeCitation} onClose={() => setActiveCitation(null)} />
    </motion.div>
  );
}