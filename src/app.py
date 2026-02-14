import sys
import time

from flask import Flask, g, request
from prometheus_client import Counter, Histogram

from src.routes.metrics import metrics_bp
from src.routes.temperature import temperature_bp
from src.routes.version import version_bp
from src.version import VERSION

app = Flask(__name__)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path", "status"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
)


@app.before_request
def start_timer():
    g.start_time = time.perf_counter()


@app.after_request
def record_metrics(response):
    duration = time.perf_counter() - g.start_time
    route = request.url_rule.rule if request.url_rule else "unmatched"
    labels = {
        "method": request.method,
        "path": route,
        "status": str(response.status_code),
    }
    HTTP_REQUESTS_TOTAL.labels(**labels).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(**labels).observe(duration)
    return response


app.register_blueprint(metrics_bp)
app.register_blueprint(temperature_bp)
app.register_blueprint(version_bp)


def print_version() -> None:
    """Print the app version from `version.py` then exit.

    Exits with code 0 on success, 1 on failure.
    """
    if not VERSION:
        print("Error: VERSION not defined", file=sys.stderr)
        sys.exit(1)

    print(VERSION)
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print_version()
    else:
        app.run(host='127.0.0.1', port=5000)
