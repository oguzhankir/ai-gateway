/** Budget tracker component */

import { Card } from '@/components/UI/Card';
import { Alert } from '@/components/UI/Alert';

interface BudgetTrackerProps {
  currentSpend?: number;
  limit?: number;
  period?: string;
}

export function BudgetTracker({ currentSpend = 0, limit = 1000, period = 'monthly' }: BudgetTrackerProps) {
  const usageRatio = limit > 0 ? currentSpend / limit : 0;
  const percentage = Math.min(usageRatio * 100, 100);

  const getColor = () => {
    if (usageRatio >= 0.9) return 'bg-red-500';
    if (usageRatio >= 0.75) return 'bg-yellow-500';
    if (usageRatio >= 0.5) return 'bg-blue-500';
    return 'bg-green-500';
  };

  return (
    <Card title={`Budget Tracker (${period})`}>
      <div className="space-y-4">
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium">Usage</span>
            <span className="text-sm font-medium">{percentage.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className={`h-4 rounded-full transition-all ${getColor()}`}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
        <div className="flex justify-between text-sm">
          <span>${currentSpend.toFixed(2)}</span>
          <span>${limit.toFixed(2)}</span>
        </div>
        {usageRatio >= 0.9 && (
          <Alert variant="error">Budget nearly exhausted! Consider increasing limit.</Alert>
        )}
        {usageRatio >= 0.75 && usageRatio < 0.9 && (
          <Alert variant="warning">Budget usage is high. Monitor spending closely.</Alert>
        )}
      </div>
    </Card>
  );
}

