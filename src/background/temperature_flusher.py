import logging
import threading
import time

from typing import Optional

from src.services.minio_service import (
    MinioService,
    TemperatureRecord,
    build_temperature_record,
)

FLUSH_INTERVAL_SECONDS = 300

logger = logging.getLogger(__name__)

_flusher_thread_started = False
_flusher_stop_event = threading.Event()
_last_temperature_value = None
_last_temperature_fetch_time = None
_minio_service: MinioService | None = None
_temperature_records: list[TemperatureRecord] = []
_records_lock = threading.Lock()
_last_flush_time: Optional[float] = None


def flush_temperature_records() -> tuple[int, bool]:
    """Flush collected temperature records to MinIO.

    Returns:
        Tuple of (number of records stored, success flag).
    """
    global _minio_service
    if _minio_service is None:
        _minio_service = MinioService.from_env()
    if _minio_service is None:
        logger.warning("MinIO not configured; skipping temperature store.")
        return 0, False

    flushed = _flush_collected_records()
    return flushed, True


def collect_temperature_record(
    average_temperature: float,
    source_hivebox_ids: list[str],
) -> TemperatureRecord:
    global _last_temperature_value, _last_temperature_fetch_time

    _last_temperature_value = average_temperature
    _last_temperature_fetch_time = time.time()
    record = build_temperature_record(
        _last_temperature_value,
        source_hivebox_ids=source_hivebox_ids,
    )
    with _records_lock:
        _temperature_records.append(record)
    logger.debug(
        "Collected temperature %.2f from %s senseBox(es).",
        _last_temperature_value,
        len(source_hivebox_ids),
    )
    return record


def _flush_collected_records() -> int:
    global _last_flush_time
    if _minio_service is None:
        return 0

    with _records_lock:
        if not _temperature_records:
            return 0
        records_to_push = list(_temperature_records)
        _temperature_records.clear()

    _minio_service.put_temperature_records(records_to_push)
    _last_flush_time = time.time()
    logger.info(
        "Flushed %s temperature record(s) to MinIO.",
        len(records_to_push),
    )
    return len(records_to_push)


def _temperature_flusher() -> None:
    """Background job to flush collected temperature data periodically."""
    global _last_flush_time
    logger.info("Starting temperature flusher thread.")
    if _last_flush_time is None:
        _last_flush_time = time.time()

    while not _flusher_stop_event.is_set():
        if _flusher_stop_event.wait(timeout=FLUSH_INTERVAL_SECONDS):
            break
        flush_temperature_records()


def start_temperature_flusher() -> None:
    """Start background flusher once per process."""
    global _flusher_thread_started
    if _flusher_thread_started:
        return
    _flusher_thread_started = True
    thread = threading.Thread(
        target=_temperature_flusher,
        name="temperature-flusher",
        daemon=True,
    )
    thread.start()
