import numpy as np

def threshold_crossing(signal,amplitudes):
    """
    Given a signal and amplitudes assign to each point in the signal its closest amplitude value. 
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

def residual_sum_squares(x, y):
    return np.sum((x-y)**2)


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


def baseline_correction(time,signal,fs,intervals, timeUnit='ms', 
             degree = 1, method = 'poly'):
    """
    Perform baseline correction by offsetting the signal with its mean
    in the selected intervals
    Parameters:
        time - 1D array containing times of the measurements in signal
               units of `timeUnit`
        signal - time series of measurements
        intervals - interval or list of intervals from which to 
                   estimate the baseline (in ms)
        fs - sampling frequency (in Hz)
        timeUnit - units of the time vector, 'ms' or 's'
        method - `baseline` can subtract a fitted polynomial of 
                 desired degree OR subtract the mean
        degree - if method is 'poly', the degree of the polynomial
    Returns:
        original signal less the fitted baseline     
    """
    if timeUnit == 'ms':
        timeUnit = 1000
    elif timeUnit == 's':
        timeUnit = 1
    t = []
    s = []
    if type(intervals[0]) is list:
        for ival in intervals:
            t.extend(time[ int(ival[0]*fs/timeUnit) 
                           : int(ival[-1]*fs/timeUnit) 
                          ])
            s.extend(signal[ int(ival[0]*fs/timeUnit) 
                             : int(ival[-1]*fs/timeUnit) 
                           ])
    elif type(intervals[0]) in [int, float]:
        t = time[ int(intervals[0]*fs/timeUnit) 
                  : int(intervals[-1]*fs/timeUnit)
                ]
        s = signal[int(intervals[0]*fs/timeUnit)
                   : int(intervals[1]*fs/timeUnit)
                  ]

    if method == 'offset':
        offset = np.mean(s)
        output = signal - offset
    elif method == 'poly':
        coeffs = np.polyfit(t,s,degree)
        baseline = np.zeros_like(time)
        for i in range(degree+1):
            baseline+=coeffs[i]*(time**(degree-i))
        output = signal - baseline
    return output
