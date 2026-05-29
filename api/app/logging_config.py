import logging

from pythonjsonlogger.jsonlogger import JsonFormatter

from app.settings import AppSettings

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(settings: AppSettings) -> None:
    if settings.log_format == "json":
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter(_LOG_FORMAT))
        logging.basicConfig(level=settings.log_level, handlers=[handler], force=True)
    else:
        logging.basicConfig(level=settings.log_level, format=_LOG_FORMAT, force=True)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True
