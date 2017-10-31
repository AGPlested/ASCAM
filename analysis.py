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
    print(amplitudes)
    amplitudes = np.sort(amplitudes)
    print(amplitudes[:-1])
    thresholds = []
    for i, amplitude in enumerate(amplitudes[:-1]):
        threshold = (amplitudes[i+1]-amplitude)/2+amplitude
        thresholds.append(threshold)

    idealization = np.zeros(len(signal))
    for i, point in enumerate(signal):
        for n, threshold in enumerate(thresholds[:-1]):
            if threshold<point<thresholds[n+1]:
                idealization[i]=amplitudes[n]
        
    return idealization

def single_state_threshold_crossing(signal, threshold):
	"""Basic threshold crossing for single-level channels
	Parameters:
		signal - 1D time series, baseline should be zero
		threshold - value in [0,1], fractioin of the maximum aplitude 
                    that should be threshold
	Returns:
		activity = time series containing 1 for open and 0 for closed
		signal_max - maximum value of original signal
	"""
	signal_max = np.max(np.abs(signal))
	thresh_val = threshold*signal_max #actual threshold value
	activity = np.array(
	[1 if x>thresh_val else -1 if x<-thresh_val else 0 for x in signal])

	return activity, signal_max

def multilevel_threshold(signal,thetas):
    """
    Idealizes a current trace using a threshold crossing algorithm.
    
    Parameters:
        signal [1D array of floats] - the signal to be idealized
        thetas [1D array of floats] - the thresholds seperating the 
                                      different levels
        
    Returns:
        idealization [1D array of floats] - an array of the same 
                                            length as `signal` 
                                            containing the 
                                            idealization of the trace
        signalmax [float] - the maximum amplitude of the signal
    This method assumes that there are four different conductance 
    states and that their amplitudes are evenly spaced.
    """
    thetas = np.sort(thetas)
    signalmax = np.max(np.abs(signal))
    idealization = np.zeros(len(signal))
    for i in range(len(signal)):
        if thetas[0]<np.abs(signal[i])<thetas[1]:
            idealization[i] = 1/3
        elif thetas[1]<np.abs(signal[i])<thetas[2]:
            idealization[i] = 2/3
        elif thetas[2]<np.abs(signal[i]):
            idealization[i] = 1
    return idealization, signalmax

### interpolation
### estimating amplitude
### least squares quality

def baseline(time,signal,fs,intervals, timeUnit='ms', 
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
    ### maybe add cosine basis functions
