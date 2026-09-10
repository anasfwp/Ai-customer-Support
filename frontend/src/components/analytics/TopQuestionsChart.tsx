import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

interface TopQuestionsChartProps {
  questions: Array<{ question: string; count: number }>;
}

function truncate(text: string, max = 30) {
  return text.length > max ? text.slice(0, max - 1) + '…' : text;
}

export default function TopQuestionsChart({ questions }: TopQuestionsChartProps) {
  const data = questions.slice(0, 8).map((q) => ({
    question: truncate(q.question),
    fullQuestion: q.question,
    count: q.count,
  }));

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Most asked questions
        </h3>
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          Top questions from your users
        </p>
      </div>

      {data.length === 0 ? (
        <div className="flex h-56 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
          No questions asked yet
        </div>
      ) : (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
              <XAxis
                type="number"
                allowDecimals={false}
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="question"
                tick={{ fontSize: 11, fill: '#64748b' }}
                axisLine={false}
                tickLine={false}
                width={160}
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
                formatter={(value: number) => [value, 'Times asked']}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.fullQuestion ?? ''}
              />
              <Bar dataKey="count" fill="#8b5cf6" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}