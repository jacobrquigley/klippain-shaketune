# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: common_func.py
# Description: Contains common functions and constants used across the Shake&Tune
#              package for 3D printer vibration analysis and diagnostics.


import math
from typing import List, Optional, Tuple

import numpy as np
from scipy.signal import spectrogram

# Constant used to define the standard axis direction and names
AXIS_CONFIG = [
    {'axis': 'x', 'direction': (1, 0, 0), 'label': 'axis_X'},
    {'axis': 'y', 'direction': (0, 1, 0), 'label': 'axis_Y'},
    {'axis': 'a', 'direction': (1, -1, 0), 'label': 'belt_A'},
    {'axis': 'b', 'direction': (1, 1, 0), 'label': 'belt_B'},
    {'axis': 'corexz_x', 'direction': (1, 0, 1), 'label': 'belt_X'},
    {'axis': 'corexz_z', 'direction': (-1, 0, 1), 'label': 'belt_Z'},
]


def compute_spectrogram(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute a spectrogram from accelerometer data using Scipy.

    This function is adapted from Klipper's spectrogram generation to use Scipy's
    spectrogram function. It computes the Power Spectral Density (PSD) across all
    three accelerometer axes (X, Y, Z) and sums them.

    The FFT window size is automatically calculated as a power of 2 based on the
    sampling frequency, using a Kaiser window with beta=6.0 for good frequency
    resolution with moderate spectral leakage.

    Args:
        data: 2D numpy array with shape (N, 4) where columns are:
            - Column 0: Time stamps
            - Column 1: X-axis acceleration
            - Column 2: Y-axis acceleration
            - Column 3: Z-axis acceleration

    Returns:
        Tuple containing:
            - pdata: 2D array of summed PSD values across all axes
            - t: 1D array of time segment centers
            - f: 1D array of frequency bins

    Example:
        >>> data = np.array([[0, 1, 2, 3], [0.1, 1.1, 2.1, 3.1]])
        >>> psd, times, freqs = compute_spectrogram(data)
    """
    N = data.shape[0]
    Fs = N / (data[-1, 0] - data[0, 0])
    # Round up to a power of 2 for faster FFT
    M = 1 << int(0.5 * Fs - 1).bit_length()
    window = np.kaiser(M, 6.0)

    def _specgram(x):
        return spectrogram(
            x, fs=Fs, window=window, nperseg=M, noverlap=M // 2, detrend='constant', scaling='density', mode='psd'
        )

    d = {'x': data[:, 1], 'y': data[:, 2], 'z': data[:, 3]}
    f, t, pdata = _specgram(d['x'])
    for axis in 'yz':
        pdata += _specgram(d[axis])[2]
    return pdata, t, f


def compute_mechanical_parameters(
    psd: np.ndarray, freqs: np.ndarray, min_freq: Optional[float] = None
) -> Tuple[Optional[float], Optional[float], Optional[int], bool]:
    """Compute natural resonant frequency and damping ratio using the half-power bandwidth method.

    This function analyzes a Power Spectral Density (PSD) curve to find the dominant
    resonant frequency and estimate the damping ratio using the half-power bandwidth
    method (also known as the -3dB method). The damping ratio is computed using
    interpolated frequencies for improved accuracy.

    The half-power bandwidth method works by:
    1. Finding the peak (resonant) frequency
    2. Finding the frequencies where power drops to 1/√2 of maximum (half-power points)
    3. Computing damping ratio from the bandwidth between half-power points

    Args:
        psd: 1D array of Power Spectral Density values
        freqs: 1D array of frequency bins corresponding to PSD values
        min_freq: Optional minimum frequency threshold. If specified, the search
            for the resonant peak will only consider frequencies above this value.
            Useful for filtering out low-frequency noise.

    Returns:
        Tuple containing:
            - fr: Resonant frequency in Hz, or None if not found
            - zeta: Damping ratio (dimensionless, typically 0-1), or None if
                    half-power points cannot be determined
            - max_power_index: Index of the peak in the PSD array, or None if not found
            - max_under_min_freq: True if the global maximum was below min_freq,
                    indicating potential issues with the measurement

    Example:
        >>> freqs = np.linspace(0, 200, 1000)
        >>> psd = np.exp(-((freqs - 50) ** 2) / 100)  # Peak at 50 Hz
        >>> fr, zeta, idx, low_warning = compute_mechanical_parameters(psd, freqs)
        >>> print(f"Resonant frequency: {fr:.1f} Hz")

    Note:
        The damping ratio computation may fail (returning None) if:
        - The peak is at the edge of the frequency range
        - The signal is too noisy to find clear half-power points
        - The bandwidth formula results in invalid mathematical operations
    """
    max_under_min_freq = False

    if min_freq is not None:
        min_freq_index = np.searchsorted(freqs, min_freq, side='left')
        if min_freq_index >= len(freqs):
            return None, None, None, max_under_min_freq
        if np.argmax(psd) < min_freq_index:
            max_under_min_freq = True
    else:
        min_freq_index = 0

    # Consider only the part of the signal above min_freq
    psd_above_min_freq = psd[min_freq_index:]
    if len(psd_above_min_freq) == 0:
        return None, None, None, max_under_min_freq

    max_power_index_above_min_freq = np.argmax(psd_above_min_freq)
    max_power_index = max_power_index_above_min_freq + min_freq_index
    fr = freqs[max_power_index]
    max_power = psd[max_power_index]

    half_power = max_power / math.sqrt(2)
    indices_below = np.where(psd[:max_power_index] <= half_power)[0]
    indices_above = np.where(psd[max_power_index:] <= half_power)[0]

    # If we are not able to find points around the half power, we can't compute the damping ratio and return None instead
    if len(indices_below) == 0 or len(indices_above) == 0:
        return fr, None, max_power_index, max_under_min_freq

    idx_below = indices_below[-1]
    idx_above = indices_above[0] + max_power_index
    freq_below_half_power = freqs[idx_below] + (half_power - psd[idx_below]) * (
        freqs[idx_below + 1] - freqs[idx_below]
    ) / (psd[idx_below + 1] - psd[idx_below])
    freq_above_half_power = freqs[idx_above - 1] + (half_power - psd[idx_above - 1]) * (
        freqs[idx_above] - freqs[idx_above - 1]
    ) / (psd[idx_above] - psd[idx_above - 1])

    bandwidth = freq_above_half_power - freq_below_half_power
    bw1 = math.pow(bandwidth / fr, 2)
    bw2 = math.pow(bandwidth / fr, 4)

    try:
        zeta = math.sqrt(0.5 - math.sqrt(1 / (4 + 4 * bw1 - bw2)))
    except ValueError:
        # If a math problem arise such as a negative sqrt term, we also return None instead for damping ratio
        return fr, None, max_power_index, max_under_min_freq

    return fr, zeta, max_power_index, max_under_min_freq


def detect_peaks(
    data: np.ndarray,
    indices: np.ndarray,
    detection_threshold: float,
    relative_height_threshold: Optional[float] = None,
    window_size: int = 5,
    vicinity: int = 3,
) -> Tuple[int, np.ndarray, np.ndarray]:
    """Detect peaks in a signal using derivative analysis and threshold filtering.

    This function finds peaks (local maxima) in a signal by analyzing where the
    derivative changes from positive to negative. It includes smoothing to reduce
    noise sensitivity and filtering based on absolute and relative height thresholds.

    The algorithm:
    1. Smooths the signal using a moving average to reduce noise
    2. Finds points where the smoothed signal transitions from increasing to decreasing
    3. Filters peaks below the absolute detection threshold
    4. Optionally filters peaks that don't stand out enough from their surroundings
    5. Refines peak positions using the original (unsmoothed) data

    Args:
        data: 1D array of signal values to analyze
        indices: 1D array of corresponding index values (e.g., frequencies or times)
            used for returning peak locations
        detection_threshold: Absolute minimum value for a peak to be considered valid.
            Peaks below this value are discarded.
        relative_height_threshold: Optional relative height filter (0-1). If specified,
            peaks must stand out by at least this fraction of their own height above
            the local minimum in their vicinity. Helps filter out peaks in noisy regions.
        window_size: Size of the moving average window for smoothing (default: 5).
            Larger values provide more smoothing but may merge nearby peaks.
        vicinity: Number of points on each side to consider when refining peak
            positions and computing relative heights (default: 3).

    Returns:
        Tuple containing:
            - num_peaks: Number of detected peaks
            - refined_peaks: 1D array of peak indices in the data array
            - peak_values: 1D array of corresponding values from the indices array

    Example:
        >>> freqs = np.linspace(0, 200, 1000)
        >>> psd = np.random.random(1000) + np.exp(-((freqs - 50) ** 2) / 100)
        >>> threshold = 0.1 * psd.max()
        >>> num, peak_indices, peak_freqs = detect_peaks(psd, freqs, threshold)
        >>> print(f"Found {num} peaks at frequencies: {peak_freqs}")
    """
    # Smooth the curve using a moving average to avoid catching peaks everywhere in noisy signals
    kernel = np.ones(window_size) / window_size
    smoothed_data = np.convolve(data, kernel, mode='valid')
    mean_pad = [np.mean(data[:window_size])] * (window_size // 2)
    smoothed_data = np.concatenate((mean_pad, smoothed_data))

    # Find peaks on the smoothed curve
    smoothed_peaks = (
        np.where((smoothed_data[:-2] < smoothed_data[1:-1]) & (smoothed_data[1:-1] > smoothed_data[2:]))[0] + 1
    )
    smoothed_peaks = smoothed_peaks[smoothed_data[smoothed_peaks] > detection_threshold]

    # Additional validation for peaks based on relative height
    valid_peaks = smoothed_peaks
    if relative_height_threshold is not None:
        valid_peaks = []
        for peak in smoothed_peaks:
            peak_height = smoothed_data[peak] - np.min(
                smoothed_data[max(0, peak - vicinity) : min(len(smoothed_data), peak + vicinity + 1)]
            )
            if peak_height > relative_height_threshold * smoothed_data[peak]:
                valid_peaks.append(peak)

    # Refine peak positions on the original curve
    refined_peaks = []
    for peak in valid_peaks:
        local_max = peak + np.argmax(data[max(0, peak - vicinity) : min(len(data), peak + vicinity + 1)]) - vicinity
        refined_peaks.append(local_max)

    num_peaks = len(refined_peaks)

    return num_peaks, np.array(refined_peaks), indices[refined_peaks]


def identify_low_energy_zones(
    power_total: np.ndarray, detection_threshold: float = 0.1
) -> List[Tuple[int, int, float]]:
    """Identify low-energy zones (valleys) in a power signal.

    This function finds contiguous regions where the signal energy is below a
    dynamically computed threshold. These zones represent "quiet" regions in the
    signal, which can indicate optimal operating conditions (e.g., speeds with
    minimal vibration).

    The threshold is computed as: mean + (max - min)/4 - detection_threshold * std

    Args:
        power_total: 1D array of power/energy values to analyze
        detection_threshold: Sensitivity parameter for valley detection (default: 0.1).
            Lower values are more sensitive (detect more valleys).
            The threshold affects how many standard deviations below the adjusted
            mean a point must be to be considered "low energy".

    Returns:
        List of tuples, each containing:
            - start: Start index of the low-energy zone
            - end: End index of the low-energy zone
            - mean_percentage: Mean energy in the zone as a percentage of the
              signal's maximum value
        The list is sorted by mean_percentage (ascending), so the "quietest"
        zones appear first.

    Example:
        >>> power = np.array([1, 0.5, 0.2, 0.1, 0.2, 0.5, 1, 0.3, 0.1, 0.3])
        >>> zones = identify_low_energy_zones(power, detection_threshold=0.5)
        >>> for start, end, energy in zones:
        ...     print(f"Zone from {start} to {end}: {energy:.1f}% of max")

    Note:
        Returns an empty list if no valleys are found or if all zones contain
        NaN values.
    """
    valleys = []

    # Calculate the a "mean + 1/4" and standard deviation of the entire power_total
    mean_energy = np.mean(power_total) + (np.max(power_total) - np.min(power_total)) / 4
    std_energy = np.std(power_total)

    # Define a threshold value as "mean + 1/4" minus a certain number of standard deviations
    threshold_value = mean_energy - detection_threshold * std_energy

    # Find valleys in power_total based on the threshold
    in_valley = False
    start_idx = 0
    for i, value in enumerate(power_total):
        if not in_valley and value < threshold_value:
            in_valley = True
            start_idx = i
        elif in_valley and value >= threshold_value:
            in_valley = False
            valleys.append((start_idx, i))

    # If the last point is still in a valley, close the valley
    if in_valley:
        valleys.append((start_idx, len(power_total) - 1))

    max_signal = np.max(power_total)

    # Calculate mean energy for each valley as a percentage of the maximum of the signal
    valley_means_percentage = []
    for start, end in valleys:
        if not np.isnan(np.mean(power_total[start:end])):
            valley_means_percentage.append((start, end, (np.mean(power_total[start:end]) / max_signal) * 100))

    # Sort valleys based on mean percentage values
    sorted_valleys = sorted(valley_means_percentage, key=lambda x: x[2])

    return sorted_valleys
