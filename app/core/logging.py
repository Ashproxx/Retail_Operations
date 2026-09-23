"""Allowlisted metadata logging; message text and payloads are excluded."""
import json
import logging


class MetadataFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {"level": record.levelname, "component": record.name}
        for key in ("event", "request_id", "status_code"):
            if hasattr(record, key):
                data[key] = getattr(record, key)
        return json.dumps(data)


def configure_logging(level: str) -> logging.Logger:
    logger = logging.getLogger("retailops")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(MetadataFormatter())
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
