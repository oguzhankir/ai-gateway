/** TypeScript types matching backend schemas */

export interface OverviewStats {
  total_requests: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_cost: number;
  avg_duration_ms: number;
  cache_hits: number;
  pii_detections: number;
}

export interface ProviderStats {
  provider: string;
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  avg_duration_ms: number;
}

export interface UserStats {
  user_id: string;
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  avg_duration_ms: number;
}

export interface TimelineStats {
  timestamp: string;
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  avg_duration_ms: number;
}

export interface RecentRequest {
  id: string;
  timestamp: string;
  provider: string;
  model: string;
  tokens: number;
  cost: number;
  duration_ms: number;
  cache_hit: boolean;
  pii_detected: boolean;
  status: string;
}

