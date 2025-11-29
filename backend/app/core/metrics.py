"""Prometheus metrics for monitoring."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

from app.config import config_manager


# Counters
total_requests = Counter(
    "ai_gateway_requests_total",
    "Total number of requests",
    ["provider", "model", "status"],
)

errors = Counter(
    "ai_gateway_errors_total",
    "Total number of errors",
    ["error_type", "provider"],
)

cache_hits = Counter(
    "ai_gateway_cache_hits_total",
    "Total number of cache hits",
)

pii_detections = Counter(
    "ai_gateway_pii_detections_total",
    "Total number of PII detections",
    ["pii_type"],
)

guardrail_violations = Counter(
    "ai_gateway_guardrail_violations_total",
    "Total number of guardrail violations",
    ["rule_name", "severity"],
)

# Histograms
request_duration = Histogram(
    "ai_gateway_request_duration_seconds",
    "Request duration in seconds",
    ["provider", "model"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

tokens_per_request = Histogram(
    "ai_gateway_tokens_per_request",
    "Number of tokens per request",
    ["token_type"],
    buckets=[100, 500, 1000, 2000, 5000, 10000, 20000],
)

cost_per_request = Histogram(
    "ai_gateway_cost_per_request_usd",
    "Cost per request in USD",
    ["provider", "model"],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)

# Gauges
active_requests = Gauge(
    "ai_gateway_active_requests",
    "Number of active requests",
)

cache_size = Gauge(
    "ai_gateway_cache_size",
    "Number of items in cache",
)

budget_usage = Gauge(
    "ai_gateway_budget_usage_ratio",
    "Budget usage ratio (0-1)",
    ["user_id", "period"],
)


def get_metrics_response() -> Response:
    """Get Prometheus metrics as HTTP response."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

