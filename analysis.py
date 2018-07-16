import numpy as np

from tools import interval_selection, piezo_selection

def threshold_crossing(signal,amplitudes):
    """
    Given a signal and amplitudes assign to each point in the signal its
    closest amplitude value.
    Amplitude of 0 is assumed to be present.
    """
    if type(amplitudes) in [list, tuple] :
        amplitudes = list(amplitudes)
        if not 0 in amplitudes:
            amplitudes.insert(0,0)
    elif type(amplitudes) in [int, float]:
        amplitudes = [0, amplitudes]
    amplitudes = np.sort(amplitudes)
    thresholds = []
    for i, amplitude in enumerate(amplitudes[:-1]):
        threshold = (amplitudes[i+1]-amplitude)/2+amplitude
        thresholds.append(threshold)

    idealization = np.zeros(len(signal))
    for i, point in enumerate(signal):
        for n, threshold in enumerate(thresholds[:-1]):
            if threshold<point<thresholds[n+1]:
                idealization[i]=amplitudes[n]
                break
    return idealization

def multilevel_threshold(signal,thresholds, maxAmplitude = False,
                         relativeThresholds = True):
    """
    performs threshold crossing for given thresholds. value should be
    given as fraction of the maximum amplitude of the signal
    Parameters:
        signal [1D array of floats] - the signal to be idealized
        thetas [1D array of floats] - the thresholds seperating the
                                      different levels
        maxAmplitude [float] - the number relative to which the
                               threshold values are given
        relativeThresholds [bool] - True is thresholds are relative
                                    to maxAmplitude or not, if false
                                    use absolute values for thresholds
    Returns:
        idealization [1D array of floats] - an array of the same
                                            length as `signal`
                                            containing the
                                            idealization of the trace
        signalmax [float] - the maximum amplitude of the signal
    """
    if maxAmplitude:
        signalmax = maxAmplitude
    else:
        maxInd = np.argmax(np.abs(signal))
        signalmax = signal[maxInd]

    thresholds.append(np.inf)

    if relativeThresholds:
        thresholds = signalmax*np.sort(thresholds)
    else:
        thresholds = np.sort(thresholds)
    N = len(thresholds)
    idealization = np.zeros(len(signal))

    for i, point in enumerate(signal):
        for n, threshold in enumerate(thresholds[:-1]):
            if np.abs(threshold)<np.abs(point)<=np.abs(thresholds[n+1]):
                idealization[i]=(n+1)/N
                break
    idealization *= signalmax
    return idealization

def baseline_correction(time, signal, fs, intervals = None, time_unit = 'ms',
                        degree = 1, method = 'poly',select_intvl = False,
                        piezo = None, select_piezo = False, active = False,
                        deviation = 0.05):
    """
    Perform baseline correction by offsetting the signal with its mean
    in the selected intervals
    Parameters:
        time - 1D array containing times of the measurements in signal
               units of `time_unit`
        signal - time series of measurements
        intervals - interval or list of intervals from which to
                   estimate the baseline (in ms)
        fs - sampling frequency (in Hz)
        time_unit - units of the time vector, 'ms' or 's'
        method - `baseline` can subtract a fitted polynomial of
                 desired degree OR subtract the mean
        degree - if method is 'poly', the degree of the polynomial
    Returns:
        original signal less the fitted baseline
    """
    if select_intvl:
        t, s = interval_selection(time, signal, intervals, fs, time_unit)
    elif select_piezo:
        t, _, s = piezo_selection(time, piezo, signal, active, deviation)
    else:
        t = time
        s = signal

    if method == 'offset':
        offset = np.mean(s)
        output = signal - offset
    elif method == 'poly':
        coeffs = np.polyfit(t,s,degree)
        baseline = np.zeros_like(time)
        for i in range(degree+1):
            baseline+=coeffs[i]*(time**(degree-i))
        output = signal - baseline
    # print("baseline_correction output:")
    # print("shape :", output.shape)
    # print('\t', output)
    return output
