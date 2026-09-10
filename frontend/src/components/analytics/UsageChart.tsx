import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { format, parseISO, subDays } from 'date-fns';
import type { ChatHistoryItem } from '../../types';

interface UsageChartProps {
  history: ChatHistoryItem[];
  days: number;
}

export default function UsageChart({ history, days }: UsageChartProps) {
  // Build a per-day count map for the last N days
  const today = new Date();
  const buckets: Record<string, number> = {};

  for (let i = days - 1; i >= 0; i--) {
    const key = format(subDays(today, i), 'yyyy-MM-dd');
    buckets[key] = 0;
  }

  history.forEach((item) => {
    try {
      const key = format(parseISO(item.created_at), 'yyyy-MM-dd');
      if (key in buckets) buckets[key] += 1;
    } catch {
      // ignore invalid dates
    }
  });

  const data = Object.entries(buckets).map(([date, count]) => ({
    date,
    label: format(parseISO(date), 'MMM d'),
    count,
  }));

  const total = data.reduce((sum, d) => sum + d.count, 0);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Queries over time
          </h3>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            {total} {total === 1 ? 'query' : 'queries'} in the last {days} days
          </p>
        </div>
      </div>

      {total === 0 ? (
        <div className="flex h-56 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
          No queries in this period
        </div>
      ) : (
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="usageGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                axisLine={false}
                tickLine={false}
                width={30}
              />
              <Tooltip
                contentStyle={{
                  background: '#1e293b',
                  border: 'none',
                  borderRadius: 8,
                  color: '#f1f5f9',
                  fontSize: 12,
                }}
                labelStyle={{ color: '#cbd5e1' }}
                formatter={(value: number) => [value, 'Queries']}
              />
              <Area
                type="monotone"
                dataKey="count"
                stroke="#6366f1"
                strokeWidth={2}
                fill="url(#usageGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}