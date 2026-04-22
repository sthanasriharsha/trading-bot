"""
logging_config.py — Sets up logging for the entire project

WHAT IS LOGGING?
Logging is like writing a diary of everything your program does.
Instead of just printing to screen (which disappears), logs are saved
to a file so you can review them later — especially useful for debugging
and for submitting evidence that your orders worked.

Python's built-in `logging` module has these severity levels:
  DEBUG    → Very detailed info, only useful while debugging
  INFO     → Normal operations (order placed, connection made)
  WARNING  → Something unexpected but not fatal
  ERROR    → Something went wrong (API error, bad input)
  CRITICAL → Program can't continue

We log both to the CONSOLE (so you see it live) and to a FILE (saved forever).
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Directory where log files will be stored
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")

# Create the logs/ directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# This flag ensures we only call setup_logging() once
_logging_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configures the root logger with two handlers:
    1. Console handler  → prints to terminal
    2. File handler     → writes to logs/trading_bot.log

    Call this ONCE at the start of your program (in cli.py).

    Args:
        level: Minimum log level to capture (default: INFO)
    """
    global _logging_configured
    if _logging_configured:
        return  # Don't configure twice

    # The "root" logger is the parent of all loggers in Python
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Format: timestamp | logger name | level | message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- Console Handler ---
    # Shows logs in your terminal while the program runs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Show INFO and above in terminal
    console_handler.setFormatter(formatter)

    # --- File Handler ---
    # RotatingFileHandler: when the file gets too big (1MB), it creates a new one
    # and keeps up to 3 old files. This prevents the log file from growing forever.
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1 * 1024 * 1024,  # 1 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # Save DEBUG and above to file
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    _logging_configured = True
    root_logger.info(f"Logging configured. Log file: {LOG_FILE}")


def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger for a specific module.

    Usage in any file:
        from bot.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Hello!")

    Using __name__ means the logger is named after the file,
    which makes it easy to see WHERE a log message came from.

    Args:
        name: Usually __name__ (the module's name)

    Returns:
        A Logger instance
    """
    return logging.getLogger(name)
