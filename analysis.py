import numpy as np

def threshold_crossing(signal, threshold):
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

def baseline(time,signal,fs,intervals, degree = 1, method = 'poly'):
    """
    Perform baseline correction by offsetting the signal with its mean
    in the selected intervals
    Parameters:
        signal - time series of measurements
        interval - interval or list of intervals from which to 
                   estimate the baseline (in ms)
        fs - sampling frequency (in Hz)
    Returns:
        original signal less the mean over the given interval       
    """
    millisecond = 1000
    t = []
    s = []
    if type(intervals[0]) is list:
        for ival in intervals:
            t.extend(time[ int(ival[0]*fs/millisecond) 
                           : int(ival[-1]*fs/millisecond) 
                          ])
            s.extend(signal[ int(ival[0]*fs/millisecond) 
                             : int(ival[-1]*fs/millisecond) 
                           ])
    elif type(intervals[0]) in (int, float):
        t = time[ int(ival[0]*fs/millisecond) 
                  : int(ival[-1]*fs/millisecond)
                ]
        s = signal[int(intervals[0]*fs/millisecond)
                   : int(intervals[1]*fs/millisecond)
                  ]

    if method == 'offset':
        offset = np.mean(s)
        return signal - offset
    elif method == 'poly':
        coeffs = np.polyfit(t,s,degree)
        baseline = np.zeros_like(time)
        for i in range(degree+1):
            baseline+=coeffs[i]*(time**(degree-i))
        return signal - baseline


##### below is the old code from when baseline was two seperate 
##### functions for offset and poly.
##### Delete it after new baseline has been tested
# def baseline(signal, fs, intervals):
#   """
#   Perform baseline correction by offsetting the signal with its mean in the 
#   selected intervals
#   Parameters:
#       signal - time series of measurements
#       interval - interval or list of intervals from which to estimate the 
#                  baseline (in ms)
#       fs - sampling frequency (in Hz)
#   Returns:
#       original signal less the mean over the given interval       
#   """
#   s = []
#   if type(intervals[0]) is list:
#       for ival in intervals:
#           s.extend(signal[ int(ival[0]*fs/1000) : int(ival[-1]*fs/1000) ])
#   elif type(intervals[0]) in (int, float):
#       s = signal[int(intervals[0]*fs/1000):int(intervals[1]*fs/1000)]

#   offset = np.mean(s)
#   signal = signal - offset
#   return signal

# def poly_baseline(time,signal,fs,intervals, degree = 1):
#     """
#     Fit a polynomial to the baseline in the selected intervals. By default the 
#     degree is one which makes this equivalent to a linear regression.
#     Parameters:
#         time [1D array of floats] - time points at which measurements where 
#                                   performed
#         signal [1D array of floats] - measurement values
#         fs [float] - sampling rate (in samples per second)
#         intervals [list] - list of intervals (in ms) that are to be used
#         degree [int] - highest order term to be included in fitting
#     Return:
#         The sloping baseline [1D array of floats]
#         """
#     t = []
#     s = []
#     for ival in intervals:
#         t.extend(time[ int(ival[0]*fs/1000) : int(ival[-1]*fs/1000) ])
#         s.extend(signal[ int(ival[0]*fs/1000) : int(ival[-1]*fs/1000) ])
#     coeffs = np.polyfit(t,s,degree)
#     baseline = np.zeros_like(time)
#     for i in range(degree+1):
#         baseline+=coeffs[i]*time**(degree-i)
#     return signal - baseline