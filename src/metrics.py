"""Custom Prometheus metrics for HiveBox application.

This module defines all custom metrics following Prometheus best practices.
All metrics are automatically registered with the default prometheus_client registry.
"""

from prometheus_client import Counter, Gauge

# Cache performance metrics
CACHE_HIT_TOTAL = Counter(
    "cache_hit_total",
    "Total number of cache hits",
    ["type"],
)

CACHE_MISS_TOTAL = Counter(
    "cache_miss_total",
    "Total number of cache misses",
    ["type"],
)

# Storage operation metrics
STORAGE_WRITE_OPERATIONS_TOTAL = Counter(
    "storage_write_operations_total",
    "Total storage write operations",
    ["type", "status"],
)

# Temperature workflow metrics
TEMPERATURE_REQUESTS_TOTAL = Counter(
    "temperature_requests_total",
    "Total temperature endpoint requests",
    ["status"],
)

TEMPERATURE_DATA_AGE_SECONDS = Gauge(
    "temperature_data_age_seconds",
    "Age in seconds of the most recent temperature value",
)
