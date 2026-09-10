import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

interface AnsweredPieChartProps {
  answered: number;
  fallback: number;
}

const COLORS = ['#10b981', '#f59e0b'];

export default function AnsweredPieChart({ answered, fallback }: AnsweredPieChartProps) {
  const total = answered + fallback;

  const data = [
    { name: 'Answered', value: answered },
    { name: 'Fallback', value: fallback },
  ];

  const answeredPct = total > 0 ? Math.round((answered / total) * 100) : 0;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Answer quality
        </h3>
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          Answered vs fallback responses
        </p>
      </div>

      {total === 0 ? (
        <div className="flex h-56 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
          No data yet
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-around">
          <div className="relative h-40 w-40">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={2}
                  stroke="none"
                >
                  {data.map((_, i) => (
                    <Cell key={i} fill={COLORS[i]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#1e293b',
                    border: 'none',
                    borderRadius: 8,
                    color: '#f1f5f9',
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {answeredPct}%
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">answered</span>
            </div>
          </div>

          <div className="space-y-3">
            {data.map((entry, i) => (
              <div key={entry.name} className="flex items-center gap-3">
                <span
                  className="h-3 w-3 rounded-full"
                  style={{ background: COLORS[i] }}
                />
                <div>
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    {entry.name}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {entry.value} {entry.value === 1 ? 'query' : 'queries'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}