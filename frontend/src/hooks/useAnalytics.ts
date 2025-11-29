/** React Query hooks for analytics data */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { OverviewStats, ProviderStats, UserStats, TimelineStats, RecentRequest } from '@/lib/types';

export function useOverviewStats(startDate?: string, endDate?: string) {
  return useQuery<OverviewStats>({
    queryKey: ['overview', startDate, endDate],
    queryFn: () => api.getOverviewStats(startDate, endDate),
    staleTime: 30000, // Consider data fresh for 30 seconds
    refetchOnWindowFocus: false,
  });
}

export function useProviderStats(startDate?: string, endDate?: string) {
  return useQuery<ProviderStats[]>({
    queryKey: ['providers', startDate, endDate],
    queryFn: () => api.getProviderStats(startDate, endDate),
    staleTime: 30000, // Consider data fresh for 30 seconds
    refetchOnWindowFocus: false,
  });
}

export function useUserStats(startDate?: string, endDate?: string, limit = 100) {
  return useQuery<UserStats[]>({
    queryKey: ['users', startDate, endDate, limit],
    queryFn: () => api.getUserStats(startDate, endDate, limit),
    staleTime: 30000, // Consider data fresh for 30 seconds
    refetchOnWindowFocus: false,
  });
}

export function useTimeline(
  startDate: string,
  endDate: string,
  granularity: 'hour' | 'day' | 'week' | 'month' = 'hour'
) {
  return useQuery<TimelineStats[]>({
    queryKey: ['timeline', startDate, endDate, granularity],
    queryFn: () => api.getTimeline(startDate, endDate, granularity),
    staleTime: 30000, // Consider data fresh for 30 seconds
    refetchOnWindowFocus: false,
  });
}

export function useRecentRequests(limit = 10) {
  return useQuery<RecentRequest[]>({
    queryKey: ['recent', limit],
    queryFn: () => api.getRecentRequests(limit),
    refetchInterval: 30000, // Refresh every 30 seconds (reduced from 5s)
    staleTime: 10000, // Consider data fresh for 10 seconds
  });
}

export function useLiveStats() {
  return useQuery({
    queryKey: ['live'],
    queryFn: () => api.getLiveStats(),
    refetchInterval: 30000, // Refresh every 30 seconds (reduced from 5s)
    staleTime: 10000, // Consider data fresh for 10 seconds
  });
}

export function useGuardrailViolations(limit = 100) {
  return useQuery({
    queryKey: ['guardrail-violations', limit],
    queryFn: () => api.getGuardrailViolations(limit),
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 30000, // Consider data fresh for 30 seconds
    refetchOnWindowFocus: false,
  });
}

