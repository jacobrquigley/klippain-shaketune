# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: exceptions.py
# Description: Custom exception classes for Shake&Tune error handling


class ShakeTuneError(Exception):
    """Base exception for all Shake&Tune errors.

    All custom exceptions in Shake&Tune should inherit from this class
    to allow for catching all Shake&Tune-specific errors with a single
    except clause.
    """


class MeasurementError(ShakeTuneError):
    """Raised when measurement data is invalid or cannot be processed.

    This exception is raised when:
    - Measurement data is missing required fields
    - Measurement data format is incorrect
    - No measurements are available for processing
    - Accelerometer data cannot be retrieved
    """


class ConfigurationError(ShakeTuneError):
    """Raised when configuration is invalid or missing.

    This exception is raised when:
    - Required configuration parameters are missing
    - Configuration values are out of valid range
    - Configuration file cannot be read or parsed
    """


class ComputationError(ShakeTuneError):
    """Raised when a computation fails or produces invalid results.

    This exception is raised when:
    - Signal processing operations fail
    - Mathematical operations produce invalid results
    - Required data for computation is missing
    """


class FileOperationError(ShakeTuneError):
    """Raised when file operations fail.

    This exception is raised when:
    - Output files cannot be created or written
    - Input files cannot be read or parsed
    - Temporary files cannot be managed
    """


class GraphCreationError(ShakeTuneError):
    """Raised when graph creation fails.

    This exception is raised when:
    - Plotting operations fail
    - Graph configuration is invalid
    - Output target is not defined
    """
