# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# Tests for console_output.py

import pytest

from shaketune.helpers.console_output import ConsoleOutput, LogLevel


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_level_ordering(self):
        """Test that log levels are properly ordered."""
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.INFO < LogLevel.WARNING
        assert LogLevel.WARNING < LogLevel.ERROR

    def test_level_values(self):
        """Test that log levels have expected integer values."""
        assert LogLevel.DEBUG == 10
        assert LogLevel.INFO == 20
        assert LogLevel.WARNING == 30
        assert LogLevel.ERROR == 40


class TestConsoleOutput:
    """Tests for ConsoleOutput class."""

    def setup_method(self):
        """Reset ConsoleOutput state before each test."""
        ConsoleOutput._output_func = None
        ConsoleOutput._log_level = LogLevel.INFO
        ConsoleOutput._logger = None

    def test_print_without_callback(self, capsys):
        """Test that print works without a callback (uses stdout)."""
        ConsoleOutput.print('Test message')
        captured = capsys.readouterr()
        assert 'Test message' in captured.out

    def test_print_with_callback(self):
        """Test that print uses callback when registered."""
        captured_messages = []

        def callback(msg):
            captured_messages.append(msg)

        ConsoleOutput.register_output_callback(callback)
        ConsoleOutput.print('Test message')

        assert len(captured_messages) == 1
        assert 'Test message' in captured_messages[0]

    def test_info_level(self, capsys):
        """Test info level logging."""
        ConsoleOutput.info('Info message')
        captured = capsys.readouterr()
        assert 'Info message' in captured.out

    def test_warning_level(self, capsys):
        """Test warning level logging."""
        ConsoleOutput.warning('Warning message')
        captured = capsys.readouterr()
        assert 'Warning:' in captured.out
        assert 'Warning message' in captured.out

    def test_error_level(self, capsys):
        """Test error level logging."""
        ConsoleOutput.error('Error message')
        captured = capsys.readouterr()
        assert 'Error:' in captured.out
        assert 'Error message' in captured.out

    def test_debug_level_hidden_by_default(self, capsys):
        """Test that debug messages are hidden when log level is INFO."""
        ConsoleOutput.set_log_level(LogLevel.INFO)
        ConsoleOutput.debug('Debug message')
        captured = capsys.readouterr()
        assert 'Debug message' not in captured.out

    def test_debug_level_shown_when_enabled(self, capsys):
        """Test that debug messages are shown when log level is DEBUG."""
        ConsoleOutput.set_log_level(LogLevel.DEBUG)
        ConsoleOutput.debug('Debug message')
        captured = capsys.readouterr()
        assert 'Debug message' in captured.out

    def test_set_log_level(self, capsys):
        """Test that set_log_level filters messages correctly."""
        ConsoleOutput.set_log_level(LogLevel.ERROR)

        ConsoleOutput.info('Info message')
        ConsoleOutput.warning('Warning message')
        ConsoleOutput.error('Error message')

        captured = capsys.readouterr()
        assert 'Info message' not in captured.out
        assert 'Warning message' not in captured.out
        assert 'Error message' in captured.out

    def test_callback_with_levels(self):
        """Test that level methods work with callback."""
        captured_messages = []

        def callback(msg):
            captured_messages.append(msg)

        ConsoleOutput.register_output_callback(callback)
        ConsoleOutput.info('Info')
        ConsoleOutput.warning('Warning')
        ConsoleOutput.error('Error')

        assert len(captured_messages) == 3

    def test_register_none_callback(self, capsys):
        """Test registering None as callback reverts to stdout."""
        def callback(msg):
            pass

        ConsoleOutput.register_output_callback(callback)
        ConsoleOutput.register_output_callback(None)
        ConsoleOutput.print('Test message')

        captured = capsys.readouterr()
        assert 'Test message' in captured.out
