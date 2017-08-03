import numpy as np
from scipy.signal import gaussian

def apply_filter(
	data,
	filter,
	method = 'convolution'):
	"""
	filename must be a string
	for now datatype should be using numpy types such as 'np.int16'
	the entire file is read assuming datatype so header length should be specified in words of the same bit length
	cutoff_frequency should be supplied in units of sampling rate
	filter_type does not need to be set until/unless we start using other filters
	method allows for using scipy fft convolve which might be faster for large data sets
	"""
	if method == 'fft':
	    from scipy.signal import fftconvolve
	    filtered_data = fftconvolve(data,filter)
	elif method == 'convolution':
	    filtered_data = np.convolve(data,filter,mode='same')
	else: raise KeyError('Method should be either "convolution" or "fft".')

	return filtered_data

def Gaussian(cutoff_frequency):
	"""This calculates the coefficients for a disrete Gaussian filter
	as described in equation A10 in ch19BB
	Parameters:
		cutoff_frequency - should be given in units of samples
	"""
	sigma = .1325/cutoff_frequency
	# M = np.int(8*sigma)
	# we might want to use the scipy Gaussian filter 
	#since scipy probably has a better implementation, 
	#however it does not do the light filtering described
	#in the blue book, i.e. when the cutoff frequency is too high
	#scipy will not filter at all compared to the light filtering
	#using the neighbours

	if sigma >= .62: #normal filtering
	    n = np.int(4*sigma)
	    non_neg_ind_coefficients = np.zeros(n+1)
	    for index in range(n+1):
	        non_neg_ind_coefficients[index] = 1/(np.sqrt(2*np.pi)*sigma)*np.exp(-index**2/(2*sigma**2))
	        negative_ind_coeff = non_neg_ind_coefficients[:0:-1]
	    coefficients = np.hstack((negative_ind_coeff,non_neg_ind_coefficients))
	else: #light filtering as described in blue book
		coefficients = np.zeros(3)
		coefficients[0] = sigma*sigma/2
		coefficients[1] = 1 - 2*coefficients[0]
		coefficients[2] = coefficients[0]

	return coefficients
