import { AnimatePresence } from 'framer-motion';
import { FileText } from 'lucide-react';
import DocumentCard from './DocumentCard';
import { Skeleton } from '../ui/Skeleton';
import type { Document } from '../../types';

interface DocumentListProps {
  documents: Document[];
  isLoading: boolean;
  deletingId: string | null;
  onDelete: (documentId: string) => void;
  onShare: (document: Document) => void;
}

export default function DocumentList({
  documents,
  isLoading,
  deletingId,
  onDelete,
  onShare,
}: DocumentListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
          >
            <Skeleton className="h-11 w-11 rounded-xl" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center dark:border-slate-700 dark:bg-slate-900/50">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800">
          <FileText className="h-5 w-5 text-slate-400" />
        </div>
        <p className="mt-4 text-sm font-medium text-slate-900 dark:text-slate-100">
          No documents yet
        </p>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Upload your first document above to get started
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <AnimatePresence initial={false}>
        {documents.map((doc) => (
          <DocumentCard
            key={doc.id}
            document={doc}
            onDelete={onDelete}
            onShare={onShare}
            isDeleting={deletingId === doc.id}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}