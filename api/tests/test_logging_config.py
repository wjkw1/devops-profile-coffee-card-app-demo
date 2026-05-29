import logging

import pytest

from app.logging_config import configure_logging
from app.settings import AppSettings


@pytest.fixture(autouse=True)
def _restore_logging():
    root = logging.root
    saved_level = root.level
    saved_handlers = root.handlers[:]

    uvicorn_state = {
        name: (logging.getLogger(name).handlers[:], logging.getLogger(name).propagate)
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access")
    }

    yield

    root.setLevel(saved_level)
    root.handlers[:] = saved_handlers

    for name, (handlers, propagate) in uvicorn_state.items():
        lg = logging.getLogger(name)
        lg.handlers[:] = handlers
        lg.propagate = propagate


class TestConfigureLogging:
    def test_text_format_sets_root_level(self):
        configure_logging(AppSettings(log_format="text", log_level="WARNING"))
        assert logging.root.level == logging.WARNING

    def test_json_format_sets_root_level(self):
        configure_logging(AppSettings(log_format="json", log_level="DEBUG"))
        assert logging.root.level == logging.DEBUG

    def test_uvicorn_loggers_propagate_after_configure(self):
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            logging.getLogger(name).propagate = False

        configure_logging(AppSettings())

        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            assert logging.getLogger(name).propagate is True

    def test_uvicorn_handlers_cleared_after_configure(self):
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            logging.getLogger(name).addHandler(logging.StreamHandler())

        configure_logging(AppSettings())

        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            assert logging.getLogger(name).handlers == []
