import numpy as np

def apply_filter(
	signal,
	window,
	method = 'convolution'):
	"""
	filename must be a string
	for now datatype should be using numpy types such as 'np.int16'
	the entire file is read assuming datatype so header length should 
	be specified in words of the same bit length
	filterFrequency should be supplied in units of sampling rate
	filter_type does not need to be set until/unless we start using 
	other filters
	method allows for using scipy fft convolve which might be faster 
	for large signal sets
	"""
	if method == 'fft':
	    from scipy.signal import fftconvolve
	    output = fftconvolve(signal, window, mode='same')
	elif method == 'convolution':
	    output = np.convolve(signal, window, mode='same')
	else: raise KeyError(
					'Method should be either "convolution" or "fft".')

	return output

def gaussian_window(filterFrequency, samplingRate = 4e4):
	"""This calculates the coefficients for a disrete Gaussian filter
	as described in equation A10 in chapter 19 in the blue book
	Parameters:
		filterFrequency - should be given in units Hz
		samplingRate - units of Hz
	"""
	filterFrequency /= samplingRate
	sigma = .1325/filterFrequency

	if sigma >= .62: # filter as normal
	    n = np.int(4*sigma)
	    non_neg_ind_coefficients = np.zeros(n+1)
	    for index in range(n+1):
	        non_neg_ind_coefficients[index] = (1/(np.sqrt(2*np.pi)
	        								   *sigma)
	        								   *np.exp(-index**2
	        								   /(2*sigma**2)))
	        negative_ind_coeff = non_neg_ind_coefficients[:0:-1]
	    coefficients = np.hstack((negative_ind_coeff,
	    						  non_neg_ind_coefficients))
	else: # light filtering as described in blue book
		coefficients = np.zeros(3)
		coefficients[0] = sigma*sigma/2
		coefficients[1] = 1 - 2*coefficients[0]
		coefficients[2] = coefficients[0]

	return coefficients

def gaussian_filter(signal, filterFrequency, samplingRate = 4e4,
				    method='convolution'):
	window = gaussian_window(filterFrequency, samplingRate)
	output = apply_filter(signal, window, method)
	return output