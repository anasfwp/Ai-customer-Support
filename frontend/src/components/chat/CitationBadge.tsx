import { FileText } from 'lucide-react';
import type { Citation } from '../../types';

interface CitationBadgeProps {
  citation: Citation;
  onClick: () => void;
}

export default function CitationBadge({ citation, onClick }: CitationBadgeProps) {
  const label = citation.section
    ? `${citation.document_name} · ${citation.section}`
    : `${citation.document_name}${citation.page ? ` · p. ${citation.page}` : ''}`;

  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 transition hover:border-indigo-300 hover:bg-indigo-100 dark:border-indigo-900/50 dark:bg-indigo-950/40 dark:text-indigo-300 dark:hover:border-indigo-800 dark:hover:bg-indigo-900/40"
      title={label}
    >
      <FileText className="h-3 w-3 shrink-0" />
      <span className="truncate">{label}</span>
    </button>
  );
}