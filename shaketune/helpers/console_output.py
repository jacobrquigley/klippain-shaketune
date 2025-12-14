# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: console_output.py
# Description: Defines the ConsoleOutput class for printing output to stdout or an alternative
#              callback function, such as the Klipper console. Provides logging levels for
#              better observability and debugging.


import io
import logging
from enum import IntEnum
from typing import Callable, Optional


class LogLevel(IntEnum):
    """Log levels for ConsoleOutput messages."""

    DEBUG = logging.DEBUG  # 10
    INFO = logging.INFO  # 20
    WARNING = logging.WARNING  # 30
    ERROR = logging.ERROR  # 40


class ConsoleOutput:
    """Print output to stdout or to an alternative like the Klipper console through a callback.

    This class provides a centralized logging mechanism for Shake&Tune with support for
    different log levels (DEBUG, INFO, WARNING, ERROR). When running as a Klipper plugin,
    output is sent to the Klipper console via a registered callback. When running standalone,
    output goes to stdout with optional Python logging integration.

    Example:
        # Register Klipper callback (done automatically when loaded as plugin)
        ConsoleOutput.register_output_callback(gcode.respond_info)

        # Log messages at different levels
        ConsoleOutput.debug('Detailed debug info')
        ConsoleOutput.info('Normal operation info')
        ConsoleOutput.warning('Something unexpected happened')
        ConsoleOutput.error('An error occurred')

        # Legacy print method (equivalent to info level)
        ConsoleOutput.print('Hello world')
    """

    _output_func: Optional[Callable[[str], None]] = None
    _log_level: LogLevel = LogLevel.INFO
    _logger: Optional[logging.Logger] = None

    @classmethod
    def register_output_callback(cls, output_func: Optional[Callable[[str], None]]) -> None:
        """Register a callback function for output (e.g., Klipper's gcode.respond_info).

        Args:
            output_func: Callable that accepts a string message, or None to use stdout
        """
        cls._output_func = output_func

    @classmethod
    def set_log_level(cls, level: LogLevel) -> None:
        """Set the minimum log level for messages to be output.

        Messages below this level will be silently ignored.

        Args:
            level: Minimum LogLevel for output
        """
        cls._log_level = level
        if cls._logger:
            cls._logger.setLevel(level)

    @classmethod
    def configure_logger(cls, name: str = 'shaketune', level: Optional[LogLevel] = None) -> logging.Logger:
        """Configure and return a Python logger for file-based logging.

        This enables logging to files in addition to console output, useful for
        debugging and diagnostics.

        Args:
            name: Logger name (default: 'shaketune')
            level: Optional log level override

        Returns:
            Configured logging.Logger instance
        """
        cls._logger = logging.getLogger(name)
        cls._logger.setLevel(level or cls._log_level)
        return cls._logger

    @classmethod
    def _output(cls, message: str, level: LogLevel) -> None:
        """Internal method to output a message at a specific level.

        Args:
            message: Message to output
            level: Log level of the message
        """
        if level < cls._log_level:
            return

        # Log to Python logger if configured
        if cls._logger:
            cls._logger.log(level, message.rstrip())

        # Output to callback or stdout
        if not cls._output_func:
            print(message, end='')
        else:
            cls._output_func(message)

    @classmethod
    def debug(cls, msg: str) -> None:
        """Log a debug message (detailed information for diagnostics).

        Args:
            msg: Debug message
        """
        cls._output(f'[DEBUG] {msg}\n', LogLevel.DEBUG)

    @classmethod
    def info(cls, msg: str) -> None:
        """Log an info message (normal operation information).

        Args:
            msg: Info message
        """
        cls._output(f'{msg}\n', LogLevel.INFO)

    @classmethod
    def warning(cls, msg: str) -> None:
        """Log a warning message (unexpected but non-fatal condition).

        Args:
            msg: Warning message
        """
        cls._output(f'Warning: {msg}\n', LogLevel.WARNING)

    @classmethod
    def error(cls, msg: str) -> None:
        """Log an error message (error condition that may affect operation).

        Args:
            msg: Error message
        """
        cls._output(f'Error: {msg}\n', LogLevel.ERROR)

    @classmethod
    def print(cls, *args, **kwargs) -> None:
        """Print output (legacy method, equivalent to info level).

        This method maintains backward compatibility with existing code.
        For new code, prefer using the level-specific methods (info, warning, error).

        Args:
            *args: Arguments to print
            **kwargs: Keyword arguments passed to print()
        """
        if not cls._output_func:
            print(*args, **kwargs)
            return

        with io.StringIO() as mem_output:
            print(*args, file=mem_output, **kwargs)
            output = mem_output.getvalue()
            # Log to Python logger if configured
            if cls._logger:
                cls._logger.info(output.rstrip())
            cls._output_func(output)
