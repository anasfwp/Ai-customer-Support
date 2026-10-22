import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Lock, Share2, Users, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Skeleton } from '../ui/Skeleton';
import { useTeam } from '../../hooks/useTeam';
import type { Document, DocumentAccessUpdate, DocumentVisibility } from '../../types';
import { cn } from '../../utils/cn';

interface ShareModalProps {
  document: Document | null;
  isSaving: boolean;
  onClose: () => void;
  onSave: (access: DocumentAccessUpdate) => Promise<void>;
}

const options: { value: DocumentVisibility; label: string; hint: string; icon: typeof Users }[] = [
  { value: 'everyone', label: 'Everyone in your company', hint: 'All team members can find it in chat', icon: Users },
  { value: 'restricted', label: 'Only specific people', hint: 'Plus the owner and admins, who always have access', icon: Lock },
];

export default function ShareModal({ document, isSaving, onClose, onSave }: ShareModalProps) {
  const { members, isLoading } = useTeam(document !== null);
  const [visibility, setVisibility] = useState<DocumentVisibility>('everyone');
  const [selected, setSelected] = useState<Set<string>>(new Set());

  // Start from the document's current sharing each time the modal opens
  useEffect(() => {
    if (document) {
      setVisibility(document.visibility);
      setSelected(new Set(document.shared_with));
    }
  }, [document]);

  useEffect(() => {
    if (!document) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [document, onClose]);

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  // The owner and admins can always see it, so only regular members are picked
  const pickable = members.filter((m) => !m.is_admin && m.email !== document?.owner_email);

  return (
    <AnimatePresence>
      {document && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm"
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="share-title"
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.15 }}
            className="fixed left-1/2 top-1/2 z-50 flex max-h-[85vh] w-[90vw] max-w-lg -translate-x-1/2 -translate-y-1/2 flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="mb-5 flex items-start justify-between gap-4">
              <div className="flex min-w-0 items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-50 dark:bg-indigo-500/10">
                  <Share2 className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                </div>
                <div className="min-w-0">
                  <h3 id="share-title" className="text-base font-semibold text-slate-900 dark:text-slate-100">
                    Who can see this document?
                  </h3>
                  <p className="mt-0.5 truncate text-sm text-slate-500 dark:text-slate-400">
                    {document.filename}
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

            <div className="space-y-2" role="radiogroup" aria-label="Visibility">
              {options.map((opt) => (
                <label
                  key={opt.value}
                  className={cn(
                    'flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition',
                    visibility === opt.value
                      ? 'border-indigo-500 bg-indigo-50/60 dark:border-indigo-400 dark:bg-indigo-500/10'
                      : 'border-slate-200 hover:border-slate-300 dark:border-slate-800 dark:hover:border-slate-700',
                  )}
                >
                  <input
                    type="radio"
                    name="visibility"
                    value={opt.value}
                    checked={visibility === opt.value}
                    onChange={() => setVisibility(opt.value)}
                    className="mt-1 accent-indigo-600"
                  />
                  <opt.icon className="mt-0.5 h-4 w-4 shrink-0 text-slate-500 dark:text-slate-400" />
                  <span>
                    <span className="block text-sm font-medium text-slate-900 dark:text-slate-100">{opt.label}</span>
                    <span className="block text-xs text-slate-500 dark:text-slate-400">{opt.hint}</span>
                  </span>
                </label>
              ))}
            </div>

            {visibility === 'restricted' && (
              <div className="mt-4 min-h-0 flex-1 overflow-y-auto">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  Share with
                </p>
                {isLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-9 w-full" />
                    <Skeleton className="h-9 w-full" />
                  </div>
                ) : pickable.length === 0 ? (
                  <p className="rounded-lg border border-dashed border-slate-300 px-3 py-4 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
                    No other members yet. An admin can add them in Settings → Team.
                  </p>
                ) : (
                  <ul className="space-y-1">
                    {pickable.map((m) => (
                      <li key={m.id}>
                        <label className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-700 transition hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800">
                          <input
                            type="checkbox"
                            checked={selected.has(m.id)}
                            onChange={() => toggle(m.id)}
                            className="accent-indigo-600"
                          />
                          <span className="truncate">{m.email}</span>
                        </label>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" onClick={onClose}>
                Cancel
              </Button>
              <Button
                loading={isSaving}
                onClick={() =>
                  onSave({ visibility, user_ids: visibility === 'restricted' ? [...selected] : [] })
                }
              >
                Save
              </Button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
