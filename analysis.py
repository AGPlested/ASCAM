import numpy as np

# def threshold_crossing(signal, threshold):
# 	"""Basic threshold crossing for single-level channels
# 	Parameters:
# 		signal - 1D time series, baseline should be zero
# 		threshold - value in [0,1], fractioin of the maximum aplitude that should be threshold
# 	Returns:
# 		activity = time series containing 1 for open and 0 for closed
# 		signal_max - maximum value of original signal
# 	"""
# 	signal_max = np.max(np.abs(signal))
# 	thresh_val = threshold*signal_max #actual threshold value
# 	activity = np.array([1 if x>thresh_val else -1 if x<-thresh_val else 0 for x in signal])
# 	return activity, signal_max
def threshold_crossing(signal, threshold):
	"""Basic threshold crossing for single-level channels
	Parameters:
		signal - 1D time series, baseline should be zero
		threshold - value in [0,1], fractioin of the maximum aplitude that should be threshold
	Returns:
		activity = time series containing 1 for open and 0 for closed
		signal_max - maximum value of original signal
	"""
	signal_max = np.max(np.abs(signal))
	thresh_val = threshold*signal_max #actual threshold value
	activity = np.array([1 if x>thresh_val else -1 if x<-thresh_val else 0 for x in signal])

	return activity, signal_max


### interpolation
### estimating amplitude
### least squares quality
### shifting basline


def baseline(signal, interval, f_s):
	"""
	Parameters:
		signal - time series of measurements
		interval - interval from which to estimate the baseline (in ms)
		f_s - sampling frequency (in Hz)
	Returns:
		original signal less the mean over the given interval		
	"""
	interval = np.array(interval)/1000*f_s
	baseline = np.mean(signal[int(interval[0]):int(interval[1])])
	signal = signal - baseline
	return signal