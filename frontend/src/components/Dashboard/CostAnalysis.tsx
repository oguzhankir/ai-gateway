/** Cost analysis chart component */

'use client';

import { Card } from '@/components/UI/Card';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { TimelineStats } from '@/lib/types';

interface CostAnalysisProps {
  data: TimelineStats[] | undefined;
  loading: boolean;
}

export function CostAnalysis({ data, loading }: CostAnalysisProps) {
  if (loading || !data || data.length === 0) {
    return (
      <Card title="Cost Analysis">
        <div className="h-64 flex items-center justify-center text-gray-500">
          {loading ? 'Loading...' : 'No data available'}
        </div>
      </Card>
    );
  }

  const chartData = data.map((d) => ({
    time: new Date(d.timestamp).toLocaleDateString(),
    cost: d.total_cost,
  }));

  return (
    <Card title="Cost Analysis">
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip formatter={(value: number) => `$${value.toFixed(4)}`} />
          <Area type="monotone" dataKey="cost" stroke="#8884d8" fill="#8884d8" />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}

