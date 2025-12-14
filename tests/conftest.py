# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# Pytest configuration and fixtures

import numpy as np
import pytest


@pytest.fixture
def sample_accelerometer_data():
    """Generate sample accelerometer data for testing.

    Returns a 2D numpy array with shape (1000, 4) containing:
    - Column 0: Time stamps (0 to 1 second)
    - Column 1-3: Simulated acceleration data with a resonance at 50 Hz
    """
    np.random.seed(42)  # For reproducibility
    n_samples = 1000
    duration = 1.0

    time = np.linspace(0, duration, n_samples)

    # Create a signal with a resonance at 50 Hz
    freq = 50.0
    signal = np.sin(2 * np.pi * freq * time) * 1000  # Main resonance
    signal += np.sin(2 * np.pi * 120 * time) * 300   # Secondary peak
    noise = np.random.normal(0, 50, n_samples)       # Add noise

    accel_x = signal + noise
    accel_y = signal * 0.8 + np.random.normal(0, 50, n_samples)
    accel_z = np.random.normal(0, 100, n_samples)  # Z mostly noise

    data = np.column_stack([time, accel_x, accel_y, accel_z])
    return data


@pytest.fixture
def sample_psd_data():
    """Generate sample PSD data with a clear peak for testing.

    Returns:
        Tuple of (psd, freqs) arrays with a peak at 50 Hz
    """
    freqs = np.linspace(0, 200, 1000)

    # Create a PSD with a peak at 50 Hz (Q factor ~ 10)
    peak_freq = 50.0
    q_factor = 10
    bandwidth = peak_freq / q_factor

    psd = 1 / ((freqs - peak_freq) ** 2 + (bandwidth / 2) ** 2)
    psd = psd / psd.max()  # Normalize

    # Add a secondary smaller peak at 120 Hz
    psd += 0.3 / ((freqs - 120) ** 2 + 25)

    return psd, freqs


@pytest.fixture
def sample_measurement():
    """Generate a sample measurement dict for testing."""
    np.random.seed(42)
    n_samples = 500
    time = np.linspace(0, 0.5, n_samples)

    samples = [
        (t, np.sin(2 * np.pi * 50 * t) * 1000 + np.random.normal(0, 50),
         np.sin(2 * np.pi * 50 * t) * 800 + np.random.normal(0, 50),
         np.random.normal(0, 100))
        for t in time
    ]

    return {
        'name': 'test_measurement_20240101_120000',
        'samples': samples,
    }
