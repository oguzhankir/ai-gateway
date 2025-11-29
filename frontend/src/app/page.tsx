/** Main dashboard page */

'use client';

import { useState, useMemo, useEffect } from 'react';
import { useOverviewStats, useProviderStats, useRecentRequests, useTimeline, useGuardrailViolations } from '@/hooks/useAnalytics';
import { MetricsOverview } from '@/components/Dashboard/MetricsOverview';
import { ProviderComparison } from '@/components/Dashboard/ProviderComparison';
import { RecentRequests } from '@/components/Dashboard/RecentRequests';
import { TokenUsageChart } from '@/components/Dashboard/TokenUsageChart';
import { CostAnalysis } from '@/components/Dashboard/CostAnalysis';
import { BudgetTracker } from '@/components/Dashboard/BudgetTracker';
import { GuardrailAlerts } from '@/components/Dashboard/GuardrailAlerts';
import { LiveActivity } from '@/components/Dashboard/LiveActivity';
import { DateRangePicker } from '@/components/Filters/DateRangePicker';
import { ProviderFilter } from '@/components/Filters/ProviderFilter';
import { Alert } from '@/components/UI/Alert';

export default function Dashboard() {
  const [dateRange, setDateRange] = useState<{ start?: string; end?: string }>({});
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);

  // Memoize default dates to prevent query key changes on every render
  const defaultDates = useMemo(() => {
    const end = new Date();
    const start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000);
    return {
      start: start.toISOString(),
      end: end.toISOString(),
    };
  }, []); // Empty deps - only calculate once

  const timelineStart = dateRange.start || defaultDates.start;
  const timelineEnd = dateRange.end || defaultDates.end;

  const { data: overview, isLoading: overviewLoading, error: overviewError } = useOverviewStats(
    dateRange.start,
    dateRange.end
  );
  const { data: providers, isLoading: providersLoading, error: providersError } = useProviderStats(
    dateRange.start,
    dateRange.end
  );
  const { data: recent, isLoading: recentLoading, error: recentError } = useRecentRequests(10);
  const { data: timeline, isLoading: timelineLoading, error: timelineError } = useTimeline(
    timelineStart,
    timelineEnd,
    'hour'
  );
  const { data: guardrailViolations, isLoading: guardrailLoading, error: guardrailError } = useGuardrailViolations(100);

  // Check for authentication errors
  const authError = overviewError || providersError || recentError || timelineError || guardrailError;
  const isAuthError = authError && (
    (authError as any)?.response?.status === 401 ||
    (authError as any)?.message?.includes('401') ||
    (authError as any)?.message?.includes('Unauthorized')
  );

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">AI Gateway Dashboard</h1>
          <div className="flex gap-4">
            <DateRangePicker
              onChange={(start, end) => setDateRange({ start, end })}
            />
            <ProviderFilter
              selected={selectedProvider}
              onChange={setSelectedProvider}
            />
          </div>
        </div>

        {/* Error Messages */}
        {isAuthError && (
          <div className="mb-6">
            <Alert variant="error">
              <strong>Authentication Error:</strong> Please check your API key configuration. 
              The dashboard requires a valid API key to access analytics data.
            </Alert>
          </div>
        )}
        {authError && !isAuthError && (
          <div className="mb-6">
            <Alert variant="warning">
              <strong>Error loading data:</strong> {(authError as any)?.message || 'An unexpected error occurred'}
            </Alert>
          </div>
        )}

        {/* Metrics Overview */}
        <div className="mb-8">
          <MetricsOverview stats={overview} loading={overviewLoading} />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <TokenUsageChart data={timeline} loading={timelineLoading} />
          <CostAnalysis data={timeline} loading={timelineLoading} />
        </div>

        {/* Provider Comparison and Budget */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <ProviderComparison providers={providers} loading={providersLoading} />
          <BudgetTracker
            currentSpend={overview?.total_cost || 0}
            limit={1000}
            period="monthly"
          />
        </div>

        {/* Guardrail Alerts and Live Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <GuardrailAlerts alerts={guardrailViolations || []} />
          <LiveActivity requests={recent} />
        </div>

        {/* Recent Requests */}
        <div className="mb-8">
          <RecentRequests requests={recent} loading={recentLoading} />
        </div>
      </div>
    </div>
  );
}

