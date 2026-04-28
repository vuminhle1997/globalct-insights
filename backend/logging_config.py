import logging
import logging.handlers
from datetime import datetime
from pathlib import Path


def setup_logging():
    """
    Sets up logging for the main application.

    Creates a 'logs' directory if it doesn't exist and configures multiple log handlers:
    - Info logs are written to a daily rotating file with a '.info.log' suffix.
    - Error logs are written to a daily rotating file with a '.error.log' suffix.
    - Debug logs are written to a daily rotating file with a '.debug.log' suffix.
    - Logs are also output to the console.

    Returns:
        logging.Logger: Configured logger for the application.
    """
    base_dir = Path(__file__).resolve().parent

    # Define logs directory relative to the project root
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Get current date for log file names
    current_date = datetime.now().strftime("%Y_%m_%d")

    # Main application logger
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Info file handler
    info_handler = logging.handlers.TimedRotatingFileHandler(
        filename=logs_dir / f"{current_date}.info.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    info_handler.addFilter(lambda record: record.levelno <= logging.INFO)

    # Error file handler
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=logs_dir / f"{current_date}.error.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Debug file handler
    debug_handler = logging.handlers.TimedRotatingFileHandler(
        filename=logs_dir / f"{current_date}.debug.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(console_handler)

    return logger
