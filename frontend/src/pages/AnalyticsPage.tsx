import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  BarChart3,
  Download,
  FileText,
  MessageSquare,
  TrendingDown,
} from 'lucide-react';
import Layout from '../components/layout/Layout';
import StatCard from '../components/analytics/StatCard';
import UsageChart from '../components/analytics/UsageChart';
import TopQuestionsChart from '../components/analytics/TopQuestionsChart';
import AnsweredPieChart from '../components/analytics/AnsweredPieChart';
import { Skeleton } from '../components/ui/Skeleton';
import { analyticsApi } from '../api/analytics';
import { chatApi } from '../api/chat';
import { formatRelative } from '../utils/formatDate';
import { cn } from '../utils/cn';

const RANGE_OPTIONS = [
  { label: '7 days', value: 7 },
  { label: '30 days', value: 30 },
  { label: '90 days', value: 90 },
];

export default function AnalyticsPage() {
  const [range, setRange] = useState(30);

  const usageQuery = useQuery({
    queryKey: ['analytics', 'usage'],
    queryFn: () => analyticsApi.usage(),
    staleTime: 30_000,
  });

  const unansweredQuery = useQuery({
    queryKey: ['analytics', 'unanswered'],
    queryFn: () => analyticsApi.unanswered(),
    staleTime: 30_000,
  });

  const historyQuery = useQuery({
    queryKey: ['chat', 'history'],
    queryFn: () => chatApi.history(200),
    staleTime: 30_000,
  });

  const usage = usageQuery.data;
  const unanswered = unansweredQuery.data ?? [];
  const history = historyQuery.data ?? [];

  // Filter history to selected range
  const filteredHistory = useMemo(() => {
    const cutoff = Date.now() - range * 24 * 60 * 60 * 1000;
    return history.filter((h) => new Date(h.created_at).getTime() >= cutoff);
  }, [history, range]);

  const answeredCount = useMemo(
    () => filteredHistory.filter((h) => !h.fallback).length,
    [filteredHistory],
  );
  const fallbackCount = filteredHistory.length - answeredCount;

  const isLoading = usageQuery.isLoading || historyQuery.isLoading;

  const exportCSV = () => {
    const rows: string[][] = [
      ['Question', 'Answer', 'Fallback', 'Confidence', 'Created At'],
      ...history.map((h) => [
        h.question,
        h.answer.replace(/\n/g, ' '),
        h.fallback ? 'Yes' : 'No',
        h.confidence ?? '',
        h.created_at,
      ]),
    ];
    const csv = rows
      .map((row) =>
        row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','),
      )
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `chat-history-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Layout title="Analytics">
      <div className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              Analytics
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Understand how your knowledge base is performing.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex rounded-lg border border-slate-200 bg-white p-0.5 dark:border-slate-700 dark:bg-slate-900">
              {RANGE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setRange(option.value)}
                  className={cn(
                    'rounded-md px-3 py-1.5 text-xs font-medium transition',
                    range === option.value
                      ? 'bg-indigo-600 text-white'
                      : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800',
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <button
              onClick={exportCSV}
              disabled={history.length === 0}
              className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              <Download className="h-3.5 w-3.5" />
              Export CSV
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-32 rounded-2xl" />
            ))}
          </div>
        ) : (
          <>
            {/* Stat cards */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                index={0}
                label="Total queries"
                value={usage?.total_queries ?? 0}
                icon={MessageSquare}
                accent="indigo"
              />
              <StatCard
                index={1}
                label="Fallback rate"
                value={`${(usage?.fallback_rate ?? 0).toFixed(1)}%`}
                icon={TrendingDown}
                accent="amber"
                hint="Questions not found in documents"
              />
              <StatCard
                index={2}
                label="Documents"
                value={usage?.total_documents ?? 0}
                icon={FileText}
                accent="violet"
              />
              <StatCard
                index={3}
                label="Content gaps"
                value={unanswered.length}
                icon={AlertCircle}
                accent="emerald"
                hint="Unanswered questions to review"
              />
            </div>

            {/* Charts row 1 */}
            <div className="grid gap-4 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <UsageChart history={filteredHistory} days={range} />
              </div>
              <AnsweredPieChart answered={answeredCount} fallback={fallbackCount} />
            </div>

            {/* Charts row 2 */}
            <div className="grid gap-4 lg:grid-cols-2">
              <TopQuestionsChart questions={usage?.top_questions ?? []} />

              {/* Unanswered questions list */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                      Content gaps
                    </h3>
                    <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                      Questions the AI couldn&apos;t answer — add docs to fix
                    </p>
                  </div>
                  <BarChart3 className="h-4 w-4 text-slate-400" />
                </div>

                {unanswered.length === 0 ? (
                  <div className="flex h-56 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
                    No content gaps detected 🎉
                  </div>
                ) : (
                  <ul className="max-h-64 space-y-2 overflow-y-auto pr-1">
                    {unanswered.map((item, i) => (
                      <motion.li
                        key={`${item.question}-${i}`}
                        initial={{ opacity: 0, x: -6 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.2, delay: i * 0.02 }}
                        className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2.5 dark:border-slate-800 dark:bg-slate-950"
                      >
                        <p className="text-sm text-slate-700 dark:text-slate-200">
                          {item.question}
                        </p>
                        <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">
                          {formatRelative(item.created_at)}
                        </p>
                      </motion.li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}