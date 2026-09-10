import { AnimatePresence, motion } from 'framer-motion';
import { FileText, X } from 'lucide-react';
import type { Citation } from '../../types';

interface CitationModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export default function CitationModal({ citation, onClose }: CitationModalProps) {
  return (
    <AnimatePresence>
      {citation && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.15 }}
            className="fixed left-1/2 top-1/2 z-50 w-[90vw] max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="mb-4 flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-50 dark:bg-indigo-500/10">
                  <FileText className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                    Source document
                  </h3>
                  <p className="mt-0.5 truncate text-sm text-slate-500 dark:text-slate-400">
                    {citation.document_name}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                aria-label="Close"
                className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3 text-sm">
              {citation.section && (
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Section</span>
                  <span className="font-medium text-slate-900 dark:text-slate-100">
                    {citation.section}
                  </span>
                </div>
              )}
              {citation.page != null && (
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Page</span>
                  <span className="font-medium text-slate-900 dark:text-slate-100">
                    {citation.page}
                  </span>
                </div>
              )}
              {citation.similarity != null && (
                <div>
                  <div className="mb-1.5 flex items-center justify-between">
                    <span className="text-slate-500 dark:text-slate-400">
                      Relevance
                    </span>
                    <span className="font-medium text-slate-900 dark:text-slate-100">
                      {Math.round(citation.similarity * 100)}%
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(citation.similarity * 100, 100)}%` }}
                      transition={{ duration: 0.4, ease: 'easeOut' }}
                      className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="mt-5 flex items-center gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-slate-950">
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Document ID:{' '}
                <span className="font-mono text-slate-700 dark:text-slate-300">
                  {citation.document_id.slice(0, 12)}…
                </span>
              </span>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}