import { ThumbsDown, ThumbsUp } from 'lucide-react';
import type { Message } from '../../types';
import { cn } from '../../utils/cn';

interface FeedbackButtonsProps {
  message: Message;
  onFeedback: (messageId: string, value: 'helpful' | 'unhelpful') => void;
}

export default function FeedbackButtons({ message, onFeedback }: FeedbackButtonsProps) {
  return (
    <div className="flex items-center gap-0.5">
      <button
        type="button"
        aria-label="Helpful"
        onClick={() => onFeedback(message.id, 'helpful')}
        className={cn(
          'rounded-lg p-1.5 transition',
          message.feedback === 'helpful'
            ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400'
            : 'text-slate-400 hover:bg-slate-100 hover:text-emerald-600 dark:hover:bg-slate-800 dark:hover:text-emerald-400',
        )}
      >
        <ThumbsUp className="h-3.5 w-3.5" />
      </button>
      <button
        type="button"
        aria-label="Not helpful"
        onClick={() => onFeedback(message.id, 'unhelpful')}
        className={cn(
          'rounded-lg p-1.5 transition',
          message.feedback === 'unhelpful'
            ? 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400'
            : 'text-slate-400 hover:bg-slate-100 hover:text-red-600 dark:hover:bg-slate-800 dark:hover:text-red-400',
        )}
      >
        <ThumbsDown className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}