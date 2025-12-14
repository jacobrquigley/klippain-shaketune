# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# Tests for exceptions.py

import pytest

from shaketune.exceptions import (
    ComputationError,
    ConfigurationError,
    FileOperationError,
    GraphCreationError,
    MeasurementError,
    ShakeTuneError,
)


class TestExceptionHierarchy:
    """Tests for exception class hierarchy."""

    def test_base_exception_is_exception(self):
        """Test that ShakeTuneError inherits from Exception."""
        assert issubclass(ShakeTuneError, Exception)

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from ShakeTuneError."""
        exceptions = [
            MeasurementError,
            ConfigurationError,
            ComputationError,
            FileOperationError,
            GraphCreationError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, ShakeTuneError), f'{exc_class.__name__} should inherit from ShakeTuneError'

    def test_exceptions_can_be_raised(self):
        """Test that all exceptions can be raised and caught."""
        exceptions = [
            ShakeTuneError,
            MeasurementError,
            ConfigurationError,
            ComputationError,
            FileOperationError,
            GraphCreationError,
        ]

        for exc_class in exceptions:
            with pytest.raises(exc_class):
                raise exc_class('Test message')

    def test_exceptions_preserve_message(self):
        """Test that exception messages are preserved."""
        message = 'Test error message'

        for exc_class in [ShakeTuneError, MeasurementError, ComputationError]:
            try:
                raise exc_class(message)
            except exc_class as e:
                assert str(e) == message

    def test_catch_all_with_base_exception(self):
        """Test that base exception can catch all derived exceptions."""
        exceptions_to_raise = [
            MeasurementError('measurement error'),
            ConfigurationError('config error'),
            ComputationError('computation error'),
            FileOperationError('file error'),
            GraphCreationError('graph error'),
        ]

        for exc in exceptions_to_raise:
            try:
                raise exc
            except ShakeTuneError as e:
                # Should catch all derived exceptions
                assert isinstance(e, ShakeTuneError)

    def test_specific_catch_doesnt_catch_others(self):
        """Test that specific exceptions don't catch other types."""
        with pytest.raises(ComputationError):
            try:
                raise ComputationError('computation error')
            except MeasurementError:
                pytest.fail('MeasurementError should not catch ComputationError')
