/** Live activity feed component */

'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/UI/Card';
import { formatDate } from '@/lib/utils';
import type { RecentRequest } from '@/lib/types';

interface LiveActivityProps {
  requests: RecentRequest[] | undefined;
}

export function LiveActivity({ requests }: LiveActivityProps) {
  const [displayedRequests, setDisplayedRequests] = useState<RecentRequest[]>([]);

  useEffect(() => {
    if (requests) {
      setDisplayedRequests(requests.slice(0, 10));
    }
  }, [requests]);

  return (
    <Card title="Live Activity">
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {displayedRequests.length === 0 ? (
          <p className="text-center text-gray-500 py-8">No recent activity</p>
        ) : (
          displayedRequests.map((req) => (
            <div
              key={req.id}
              className="p-3 bg-gray-50 rounded border-l-4 border-blue-500 animate-fade-in"
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-medium text-sm">{req.provider} - {req.model}</p>
                  <p className="text-xs text-gray-500 mt-1">{formatDate(req.timestamp)}</p>
                </div>
                <span
                  className={`px-2 py-1 rounded text-xs ${
                    req.status === 'completed'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {req.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}

