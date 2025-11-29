/** Guardrail alerts component */

import { Card } from '@/components/UI/Card';
import { Alert } from '@/components/UI/Alert';

interface GuardrailAlert {
  id: string;
  rule_name: string;
  severity: 'error' | 'warning' | 'info';
  message?: string;
  details?: {
    message?: string;
    [key: string]: any;
  };
  timestamp: string;
}

interface GuardrailAlertsProps {
  alerts?: GuardrailAlert[];
}

export function GuardrailAlerts({ alerts = [] }: GuardrailAlertsProps) {
  return (
    <Card title="Recent Guardrail Violations">
      {alerts.length === 0 ? (
        <p className="text-center text-gray-500 py-8">No violations in the last 24 hours</p>
      ) : (
        <div className="space-y-3">
          {alerts.slice(0, 5).map((alert) => (
            <Alert key={alert.id} variant={alert.severity === 'error' ? 'error' : 'warning'}>
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold">{alert.rule_name}</p>
                  <p className="text-sm mt-1">
                    {alert.message || alert.details?.message || 'Guardrail violation detected'}
                  </p>
                </div>
                <span className="text-xs text-gray-500">
                  {new Date(alert.timestamp).toLocaleString()}
                </span>
              </div>
            </Alert>
          ))}
        </div>
      )}
    </Card>
  );
}

