from __future__ import annotations

import logging


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for key in ("stage", "source", "symbol", "reason"):
            if not hasattr(record, key):
                setattr(record, key, "-")
        return True


def get_logger(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("navscan")
    if logger.handlers:
        return logger
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.addFilter(_ContextFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s level=%(levelname)s stage=%(stage)s source=%(source)s "
            "symbol=%(symbol)s reason=%(reason)s msg=%(message)s"
        )
    )
    logger.addHandler(handler)
    logger.propagate = False
    return logger

