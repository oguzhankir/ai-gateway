/** Recent requests component */

import { Card } from '@/components/UI/Card';
import { LoadingSpinner } from '@/components/UI/LoadingSpinner';
import { formatCost, formatTokens, formatDuration, formatDate } from '@/lib/utils';
import type { RecentRequest } from '@/lib/types';

interface RecentRequestsProps {
  requests: RecentRequest[] | undefined;
  loading: boolean;
}

export function RecentRequests({ requests, loading }: RecentRequestsProps) {
  return (
    <Card title="Recent Requests">
      {loading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Time</th>
                <th className="text-left p-2">Provider</th>
                <th className="text-left p-2">Model</th>
                <th className="text-left p-2">Tokens</th>
                <th className="text-left p-2">Cost</th>
                <th className="text-left p-2">Duration</th>
                <th className="text-left p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {requests && requests.length > 0 ? (
                requests.map((r) => (
                  <tr key={r.id} className="border-b hover:bg-gray-50">
                    <td className="p-2 text-sm">{formatDate(r.timestamp)}</td>
                    <td className="p-2">{r.provider}</td>
                    <td className="p-2 text-sm">{r.model}</td>
                    <td className="p-2">{formatTokens(r.tokens)}</td>
                    <td className="p-2">{formatCost(r.cost)}</td>
                    <td className="p-2">{formatDuration(r.duration_ms)}</td>
                    <td className="p-2">
                      <span
                        className={`px-2 py-1 rounded text-xs ${
                          r.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : r.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-gray-500">
                    No requests found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
