import { motion } from 'framer-motion';
import { FileText, Loader2, Trash2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Badge } from '../ui/Badge';
import type { Document } from '../../types';
import { formatRelative } from '../../utils/formatDate';
import { cn } from '../../utils/cn';

interface DocumentCardProps {
  document: Document;
  onDelete: (documentId: string) => void;
  isDeleting?: boolean;
}

export default function DocumentCard({
  document,
  onDelete,
  isDeleting,
}: DocumentCardProps) {
  const statusConfig = {
    processing: {
      badge: 'warning' as const,
      label: 'Processing',
      icon: Loader2,
      iconClass: 'animate-spin',
    },
    ready: {
      badge: 'success' as const,
      label: 'Ready',
      icon: CheckCircle2,
      iconClass: '',
    },
    failed: {
      badge: 'danger' as const,
      label: 'Failed',
      icon: AlertCircle,
      iconClass: '',
    },
  };

  const config = statusConfig[document.status] ?? statusConfig.processing;
  const StatusIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2 }}
      className={cn(
        'group flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 transition hover:border-slate-300 hover:shadow-sm',
        'dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700',
      )}
    >
      {/* Icon */}
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-50 to-violet-50 dark:from-indigo-950/40 dark:to-violet-950/40">
        <FileText className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
          {document.filename}
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
          <span className="inline-flex items-center gap-1">
            <StatusIcon className={cn('h-3 w-3', config.iconClass)} />
            {config.label}
          </span>
          <span className="text-slate-300 dark:text-slate-700">·</span>
          <span>
            {document.chunk_count}{' '}
            {document.chunk_count === 1 ? 'chunk' : 'chunks'}
          </span>
          <span className="text-slate-300 dark:text-slate-700">·</span>
          <span>{formatRelative(document.created_at)}</span>
        </div>
      </div>

      {/* Status badge */}
      <Badge variant={config.badge} className="hidden sm:inline-flex">
        {config.label}
      </Badge>

      {/* Delete */}
      <button
        type="button"
        onClick={() => onDelete(document.id)}
        disabled={isDeleting}
        aria-label={`Delete ${document.filename}`}
        className={cn(
          'flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition',
          'hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-500/10 dark:hover:text-red-400',
          'disabled:cursor-not-allowed disabled:opacity-50',
        )}
      >
        {isDeleting ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Trash2 className="h-4 w-4" />
        )}
      </button>
    </motion.div>
  );
}