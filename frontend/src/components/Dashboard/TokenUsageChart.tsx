/** Token usage chart component */

'use client';

import { Card } from '@/components/UI/Card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { TimelineStats } from '@/lib/types';

interface TokenUsageChartProps {
  data: TimelineStats[] | undefined;
  loading: boolean;
}

export function TokenUsageChart({ data, loading }: TokenUsageChartProps) {
  if (loading || !data || data.length === 0) {
    return (
      <Card title="Token Usage Over Time">
        <div className="h-64 flex items-center justify-center text-gray-500">
          {loading ? 'Loading...' : 'No data available'}
        </div>
      </Card>
    );
  }

  const chartData = data.map((d) => ({
    time: new Date(d.timestamp).toLocaleDateString(),
    prompt: d.total_tokens * 0.6, // Estimate
    completion: d.total_tokens * 0.4, // Estimate
    total: d.total_tokens,
  }));

  return (
    <Card title="Token Usage Over Time">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="prompt" stroke="#8884d8" name="Prompt Tokens" />
          <Line type="monotone" dataKey="completion" stroke="#82ca9d" name="Completion Tokens" />
          <Line type="monotone" dataKey="total" stroke="#ffc658" name="Total Tokens" />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}

