# API Reference

## GET /version

Returns the version of the currently deployed application.

**Parameters:** None

**Response:**

```json
{
  "version": "v0.0.1"
}
```

**Example:**

```bash
curl http://localhost:5000/version
```

---

## GET /temperature

Returns the latest average temperature captured by the background fetcher.

**Parameters:** None

**Response (Success):**

```json
{
  "average_temperature": 22.46,
  "status": "Good"
}
```

**Status Field Values:**

- `"Too Cold"`: Average temperature is less than 10°C
- `"Good"`: Average temperature is between 10°C and 36°C (inclusive)
- `"Too Hot"`: Average temperature is greater than 36°C

**Response (Error - No Data Available):**

```json
{
  "error": "No temperature data available",
  "message": "Unable to retrieve fresh temperature data from senseBoxes. Data may be unavailable or older than 1 hour."
}
```

**Status Codes:**

- `200 OK`: Temperature data retrieved successfully
- `503 Service Unavailable`: No fresh temperature data available

**Notes:**

- Fetches fresh data directly from openSenseMap (https://api.opensensemap.org)
- Falls back to the latest MinIO record when live data is unavailable
- Only includes temperature data from the last hour when recorded
- Temperature is rounded to 2 decimal places
- Configured senseBox IDs are stored in `src/services/temperature_service.py`

**Example:**

```bash
curl http://localhost:5000/temperature
```

---

## POST /store

Flushes buffered temperature measurements to MinIO.

**Parameters:** None

**Response (Success):**

```json
{
  "flushed": 3
}
```

**Response (Error - MinIO Not Configured):**

```json
{
  "error": "MinIO not configured",
  "message": "Unable to flush temperature data to MinIO."
}
```

**Status Codes:**

- `200 OK`: Records flushed (count returned)
- `503 Service Unavailable`: MinIO not configured

**Notes:**

- The background job also flushes automatically every 5 minutes.

**Example:**

```bash
curl -X POST http://localhost:5000/store
```

---

## GET /metrics

Exposes Prometheus metrics for the app.

**Metrics:**

**HTTP Request Metrics:**

- `http_requests_total{method, path, status}` (counter) - Total HTTP requests
- `http_request_duration_seconds{method, path, status}` (histogram) - HTTP request duration

**Cache Performance Metrics:**

- `cache_hit_total{type}` (counter) - Number of cache hits, labeled by cache type (e.g., `valkey`)
- `cache_miss_total{type}` (counter) - Number of cache misses, labeled by cache type

**Storage Operation Metrics:**

- `storage_write_operations_total{type, status}` (counter) - Storage write operations, labeled by type (e.g., `minio`) and status (`success`, `failed`)

**Temperature Workflow Metrics:**

- `temperature_requests_total{status}` (counter) - Count of `/temperature` endpoint requests, labeled by outcome (`success`, `no_data`, `error`)
- `temperature_data_age_seconds` (gauge) - Age in seconds of the most recent temperature value used

**Example:**

```bash
curl http://localhost:5000/metrics
```

**Sample Output:**

```
# HELP cache_hit_total Total number of cache hits
# TYPE cache_hit_total counter
cache_hit_total{type="valkey"} 42.0

# HELP cache_miss_total Total number of cache misses
# TYPE cache_miss_total counter
cache_miss_total{type="valkey"} 5.0

# HELP storage_write_operations_total Total storage write operations
# TYPE storage_write_operations_total counter
storage_write_operations_total{type="minio",status="success"} 128.0
storage_write_operations_total{type="minio",status="failed"} 2.0

# HELP temperature_requests_total Total temperature endpoint requests
# TYPE temperature_requests_total counter
temperature_requests_total{status="success"} 156.0
temperature_requests_total{status="no_data"} 3.0

# HELP temperature_data_age_seconds Age in seconds of the most recent temperature value
# TYPE temperature_data_age_seconds gauge
temperature_data_age_seconds 12.5
```

---

## GET /readyz

Returns readiness status of the application for health checks (Kubernetes readiness probe, load balancer health checks).

**Parameters:** None

**Response (Ready - 200 OK):**

```json
{
  "status": "ready",
  "sensebox": {
    "accessible": 3,
    "total": 3,
    "inaccessible": 0
  },
  "cache": {
    "age_seconds": 45,
    "max_age_seconds": 300
  }
}
```

**Response (Not Ready - 503 Service Unavailable):**

```json
{
  "status": "not_ready",
  "reason": "More than 50% of senseBoxes are inaccessible (2/3) and cached data is older than 5 minutes.",
  "sensebox": {
    "accessible": 1,
    "total": 3,
    "inaccessible": 2
  },
  "cache": {
    "age_seconds": 360,
    "max_age_seconds": 300
  }
}
```

**Status Codes:**

- `200 OK`: Service is ready (default response)
- `503 Service Unavailable`: Service is not ready (only when BOTH conditions are met: >50% senseBoxes inaccessible AND cache older than 5 minutes)

**Notes:**

- Returns 503 only when **both** conditions are true simultaneously
- Used for Kubernetes readiness probes and load balancer health checks
- Checks actual senseBox API accessibility in real-time

**Example:**

```bash
curl http://localhost:5000/readyz
```
