# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# Tests for common_func.py

import numpy as np
import pytest

from shaketune.helpers.common_func import (
    compute_mechanical_parameters,
    compute_spectrogram,
    detect_peaks,
    identify_low_energy_zones,
)


class TestComputeSpectrogram:
    """Tests for compute_spectrogram function."""

    def test_basic_spectrogram(self, sample_accelerometer_data):
        """Test that spectrogram computation returns expected shapes."""
        pdata, t, f = compute_spectrogram(sample_accelerometer_data)

        assert pdata is not None
        assert t is not None
        assert f is not None
        assert len(f) > 0
        assert len(t) > 0
        assert pdata.shape[0] == len(f)

    def test_spectrogram_frequency_range(self, sample_accelerometer_data):
        """Test that frequency bins are reasonable."""
        pdata, t, f = compute_spectrogram(sample_accelerometer_data)

        assert f[0] >= 0, 'Frequencies should start at 0 or above'
        assert f[-1] <= 1000, 'Max frequency should be reasonable for accelerometer data'

    def test_spectrogram_with_minimal_data(self):
        """Test spectrogram with minimal valid data."""
        # Create minimal data: just enough samples for FFT
        n_samples = 100
        time = np.linspace(0, 0.1, n_samples)
        data = np.column_stack([
            time,
            np.sin(2 * np.pi * 50 * time),
            np.sin(2 * np.pi * 50 * time),
            np.zeros(n_samples),
        ])

        pdata, t, f = compute_spectrogram(data)
        assert pdata is not None


class TestComputeMechanicalParameters:
    """Tests for compute_mechanical_parameters function."""

    def test_finds_resonant_frequency(self, sample_psd_data):
        """Test that resonant frequency is correctly identified."""
        psd, freqs = sample_psd_data

        fr, zeta, idx, low_warning = compute_mechanical_parameters(psd, freqs)

        assert fr is not None
        assert 45 <= fr <= 55, f'Expected resonant frequency near 50 Hz, got {fr}'
        assert not low_warning

    def test_returns_damping_ratio(self, sample_psd_data):
        """Test that damping ratio is computed."""
        psd, freqs = sample_psd_data

        fr, zeta, idx, low_warning = compute_mechanical_parameters(psd, freqs)

        # Damping ratio should be computed for a well-formed peak
        assert zeta is not None
        assert 0 < zeta < 1, f'Damping ratio should be between 0 and 1, got {zeta}'

    def test_min_freq_threshold(self, sample_psd_data):
        """Test that min_freq parameter filters low frequencies."""
        psd, freqs = sample_psd_data

        # With min_freq above the main peak, should find secondary peak
        fr, zeta, idx, low_warning = compute_mechanical_parameters(psd, freqs, min_freq=100)

        assert fr is not None
        assert fr > 100, f'Resonant frequency should be above min_freq, got {fr}'
        assert low_warning, 'Should warn that max was under min_freq'

    def test_empty_psd(self):
        """Test handling of empty PSD data."""
        psd = np.array([])
        freqs = np.array([])

        fr, zeta, idx, low_warning = compute_mechanical_parameters(psd, freqs)

        assert fr is None
        assert zeta is None

    def test_flat_psd(self):
        """Test handling of flat PSD (no clear peak)."""
        freqs = np.linspace(0, 200, 100)
        psd = np.ones_like(freqs)  # Flat PSD

        fr, zeta, idx, low_warning = compute_mechanical_parameters(psd, freqs)

        # Should still find a "peak" but damping ratio may be None
        assert fr is not None


class TestDetectPeaks:
    """Tests for detect_peaks function."""

    def test_finds_single_peak(self):
        """Test detection of a single clear peak."""
        freqs = np.linspace(0, 200, 500)
        data = np.exp(-((freqs - 100) ** 2) / 50)  # Gaussian peak at 100 Hz

        threshold = 0.1 * data.max()
        num_peaks, peaks, peak_freqs = detect_peaks(data, freqs, threshold)

        assert num_peaks >= 1
        assert len(peak_freqs) >= 1
        # Peak should be near 100 Hz
        assert any(95 <= f <= 105 for f in peak_freqs), f'Expected peak near 100 Hz, got {peak_freqs}'

    def test_finds_multiple_peaks(self):
        """Test detection of multiple peaks."""
        freqs = np.linspace(0, 200, 500)
        # Two Gaussian peaks at 50 Hz and 150 Hz
        data = np.exp(-((freqs - 50) ** 2) / 50) + np.exp(-((freqs - 150) ** 2) / 50)

        threshold = 0.1 * data.max()
        num_peaks, peaks, peak_freqs = detect_peaks(data, freqs, threshold)

        assert num_peaks >= 2, f'Expected at least 2 peaks, found {num_peaks}'

    def test_threshold_filters_small_peaks(self):
        """Test that threshold correctly filters out small peaks."""
        freqs = np.linspace(0, 200, 500)
        # One large peak and one small peak
        data = np.exp(-((freqs - 50) ** 2) / 50) + 0.05 * np.exp(-((freqs - 150) ** 2) / 50)

        # High threshold should only find the large peak
        threshold = 0.5 * data.max()
        num_peaks, peaks, peak_freqs = detect_peaks(data, freqs, threshold)

        assert num_peaks == 1, f'High threshold should find only 1 peak, found {num_peaks}'

    def test_relative_height_threshold(self):
        """Test relative height threshold filtering."""
        freqs = np.linspace(0, 200, 500)
        # Signal with noise
        np.random.seed(42)
        data = np.exp(-((freqs - 100) ** 2) / 50) + 0.1 * np.random.random(500)

        threshold = 0.1 * data.max()
        num_peaks_no_rel, _, _ = detect_peaks(data, freqs, threshold, relative_height_threshold=None)
        num_peaks_with_rel, _, _ = detect_peaks(data, freqs, threshold, relative_height_threshold=0.2)

        # Relative height threshold should reduce noise peaks
        assert num_peaks_with_rel <= num_peaks_no_rel

    def test_empty_data(self):
        """Test handling of empty data."""
        freqs = np.array([])
        data = np.array([])

        num_peaks, peaks, peak_freqs = detect_peaks(data, freqs, 0.1)

        assert num_peaks == 0
        assert len(peaks) == 0


class TestIdentifyLowEnergyZones:
    """Tests for identify_low_energy_zones function."""

    def test_finds_valleys(self):
        """Test that valleys are correctly identified."""
        # Create data with clear valley
        power = np.array([1.0, 0.8, 0.2, 0.1, 0.2, 0.8, 1.0, 0.9, 0.1, 0.2, 0.9])

        valleys = identify_low_energy_zones(power, detection_threshold=0.5)

        assert len(valleys) >= 1, 'Should find at least one valley'
        # Valleys should be sorted by energy (lowest first)
        if len(valleys) > 1:
            assert valleys[0][2] <= valleys[1][2], 'Valleys should be sorted by energy'

    def test_returns_sorted_by_energy(self):
        """Test that returned valleys are sorted by mean energy."""
        # Multiple valleys with different energies
        power = np.concatenate([
            np.ones(10) * 0.5,  # Medium valley
            np.ones(10) * 1.0,  # High
            np.ones(10) * 0.1,  # Low valley (should be first)
            np.ones(10) * 1.0,  # High
        ])

        valleys = identify_low_energy_zones(power, detection_threshold=0.3)

        if len(valleys) >= 2:
            energies = [v[2] for v in valleys]
            assert energies == sorted(energies), 'Valleys should be sorted by energy'

    def test_no_valleys_in_flat_signal(self):
        """Test that flat high-energy signal has no valleys."""
        power = np.ones(100)  # Flat signal

        valleys = identify_low_energy_zones(power, detection_threshold=0.1)

        # Flat signal shouldn't have valleys below threshold
        assert len(valleys) == 0 or all(v[2] > 50 for v in valleys)

    def test_sensitivity_parameter(self):
        """Test that detection_threshold affects sensitivity."""
        power = np.array([1.0, 0.8, 0.6, 0.4, 0.6, 0.8, 1.0])

        valleys_sensitive = identify_low_energy_zones(power, detection_threshold=0.1)
        valleys_insensitive = identify_low_energy_zones(power, detection_threshold=2.0)

        # More sensitive (lower threshold) should find more or equal valleys
        assert len(valleys_sensitive) >= len(valleys_insensitive)
