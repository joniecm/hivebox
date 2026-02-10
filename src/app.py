import logging
import os
import sys
import time
from datetime import datetime, timezone

from flask import Flask, g, request
from prometheus_client import Counter, Histogram

from src.background.temperature_flusher import start_temperature_flusher
from src.config import load_minio_config
from src.routes.metrics import metrics_bp
from src.routes.store import store_bp
from src.routes.temperature import temperature_bp
from src.routes.version import version_bp
from src.services.minio_service import MinioService
from src.version import VERSION

logger = logging.getLogger(__name__)

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


def configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    
    class UTCFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.isoformat()
    
    formatter = UTCFormatter(
        fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)


def ensure_minio_ready_or_exit() -> None:
    if (
        os.getenv("SKIP_MINIO_CHECK")
        or os.getenv("PYTEST_CURRENT_TEST")
        or "pytest" in sys.modules
    ):
        logger.info("Skipping MinIO readiness check.")
        return
    minio_service = MinioService.from_env()
    if minio_service is None:
        logger.error("MinIO configuration missing or invalid")
        sys.exit(1)
    
    max_retries = 12
    retry_delay = 2
    for attempt in range(1, max_retries + 1):
        try:
            minio_service.ensure_bucket_or_raise()
            logger.info("MinIO connection established successfully on attempt %d", attempt)
            return
        except RuntimeError as exc:
            if attempt < max_retries:
                wait_time = retry_delay * attempt
                logger.warning("Attempt %d/%d: %s. Retrying in %ds...", attempt, max_retries, exc, wait_time)
                time.sleep(wait_time)
            else:
                logger.error("Failed to connect to MinIO after %d attempts: %s", max_retries, exc)
                sys.exit(1)


def create_app() -> Flask:
    configure_logging()
    ensure_minio_ready_or_exit()

    app = Flask(__name__)
    app.config["MINIO"] = load_minio_config()
    start_temperature_flusher()

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
    app.register_blueprint(version_bp)
    app.register_blueprint(temperature_bp)
    app.register_blueprint(store_bp)

    return app


app = create_app()


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
        start_temperature_flusher()
        app.run(host="0.0.0.0", port=5000)
