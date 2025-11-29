/** Provider comparison component */

import { Card } from '@/components/UI/Card';
import { LoadingSpinner } from '@/components/UI/LoadingSpinner';
import { formatCost, formatDuration } from '@/lib/utils';
import type { ProviderStats } from '@/lib/types';

interface ProviderComparisonProps {
  providers: ProviderStats[] | undefined;
  loading: boolean;
}

export function ProviderComparison({ providers, loading }: ProviderComparisonProps) {
  return (
    <Card title="Provider Comparison">
      {loading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="space-y-4">
          {providers && providers.length > 0 ? (
            providers.map((p) => (
              <div key={p.provider} className="flex justify-between items-center p-4 bg-gray-50 rounded">
                <div>
                  <h4 className="font-semibold">{p.provider}</h4>
                  <p className="text-sm text-gray-600">{p.total_requests} requests</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold">{formatCost(p.total_cost)}</p>
                  <p className="text-sm text-gray-600">{formatDuration(p.avg_duration_ms)} avg</p>
                </div>
              </div>
            ))
          ) : (
            <p className="text-center text-gray-500 py-8">No provider data available</p>
          )}
        </div>
      )}
    </Card>
  );
}
