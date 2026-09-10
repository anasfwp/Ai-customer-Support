import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { cn } from '../../utils/cn';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  hint?: string;
  accent?: 'indigo' | 'emerald' | 'amber' | 'violet';
  index?: number;
}

const accents = {
  indigo: {
    bg: 'bg-indigo-50 dark:bg-indigo-500/10',
    text: 'text-indigo-600 dark:text-indigo-400',
  },
  emerald: {
    bg: 'bg-emerald-50 dark:bg-emerald-500/10',
    text: 'text-emerald-600 dark:text-emerald-400',
  },
  amber: {
    bg: 'bg-amber-50 dark:bg-amber-500/10',
    text: 'text-amber-600 dark:text-amber-400',
  },
  violet: {
    bg: 'bg-violet-50 dark:bg-violet-500/10',
    text: 'text-violet-600 dark:text-violet-400',
  },
};

export default function StatCard({
  label,
  value,
  icon: Icon,
  hint,
  accent = 'indigo',
  index = 0,
}: StatCardProps) {
  const styles = accents[accent];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex items-start justify-between">
        <div className={cn('flex h-10 w-10 items-center justify-center rounded-xl', styles.bg)}>
          <Icon className={cn('h-5 w-5', styles.text)} />
        </div>
      </div>
      <p className="mt-4 text-2xl font-bold text-slate-900 dark:text-slate-100">{value}</p>
      <p className="mt-0.5 text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
      {hint && <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{hint}</p>}
    </motion.div>
  );
}