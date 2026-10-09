"""Application logging configuration."""

import logging
import logging.config

from app.config import Settings


def configure_logging(settings: Settings) -> None:
    """Load logging handlers and formatters from the external config file."""
    logging.config.fileConfig(
        settings.logging_config_path,
        disable_existing_loggers=False,
    )
    logging.getLogger("app").setLevel(settings.log_level)
