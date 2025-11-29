/** Metrics overview component */

import { Card } from '@/components/UI/Card';
import { LoadingSpinner } from '@/components/UI/LoadingSpinner';
import { formatCost, formatTokens, formatDuration } from '@/lib/utils';
import type { OverviewStats } from '@/lib/types';

interface MetricsOverviewProps {
  stats: OverviewStats | undefined;
  loading: boolean;
}

export function MetricsOverview({ stats, loading }: MetricsOverviewProps) {
  const metrics: Array<{
    title: string;
    value: number | string;
    format: (v: number | string) => string;
  }> = [
    {
      title: 'Total Requests',
      value: stats?.total_requests || 0,
      format: (v: number | string) => typeof v === 'number' ? v.toLocaleString() : v,
    },
    {
      title: 'Total Tokens',
      value: stats?.total_tokens || 0,
      format: (v: number | string) => formatTokens(typeof v === 'number' ? v : parseInt(v.toString())),
    },
    {
      title: 'Total Cost',
      value: stats?.total_cost || 0,
      format: (v: number | string) => formatCost(typeof v === 'number' ? v : parseFloat(v.toString())),
    },
    {
      title: 'Avg Response Time',
      value: stats?.avg_duration_ms || 0,
      format: (v: number | string) => formatDuration(typeof v === 'number' ? v : parseInt(v.toString())),
    },
    {
      title: 'Cache Hit Rate',
      value:
        stats && stats.total_requests > 0
          ? ((stats.cache_hits / stats.total_requests) * 100).toFixed(1)
          : '0',
      format: (v: number | string) => `${v}%`,
    },
    {
      title: 'PII Detection Rate',
      value:
        stats && stats.total_requests > 0
          ? ((stats.pii_detections / stats.total_requests) * 100).toFixed(1)
          : '0',
      format: (v: number | string) => `${v}%`,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {metrics.map((metric) => (
        <Card key={metric.title} variant="outlined">
          <h3 className="text-sm font-medium text-gray-500 mb-2">{metric.title}</h3>
          {loading ? (
            <LoadingSpinner size="sm" />
          ) : (
            <p className="text-2xl font-bold">{metric.format(metric.value)}</p>
          )}
        </Card>
      ))}
    </div>
  );
}
