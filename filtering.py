import numpy as np

def apply_filter(
	signal,
	window,*args,**kwargs):
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

	# pad with constant values to reduce boundary effects and keep
	# original length of array
	padLength = int((len(window)-1)/2) # `len(window)` is always odd
	leftPad = np.ones(padLength)*signal[0]
	rightPad = np.ones(padLength)*signal[-1]
	signal = signal.flatten()
	signal = np.hstack((leftPad,signal,rightPad))
	output = np.convolve(signal, window, mode='valid')

	return output

def gaussian_window(filterFrequency, sampling_rate=4e4):
	"""This calculates the coefficients for a disrete Gaussian filter
	as described in equation A10 in chapter 19 in the blue book
	Parameters:
		filterFrequency - should be given in units Hz
		sampling_rate - units of Hz
	"""
	filterFrequency /= sampling_rate
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

def gaussian_filter(signal, filterFrequency, sampling_rate=4e4,
				    method='convolution'):
	window = gaussian_window(filterFrequency, sampling_rate)
	output = apply_filter(signal, window, method)
	return output

class ChungKennedyFilter:
	"""
	Create a "Chung-Kennedy" filter as described in
	https://doi.org/10.1016/0165-0270(91)90118-J
	"""
    def __init__(self, window_lengths, weight_exponent, weight_window,
				 apriori_f_weights=False, apriori_b_weights=False):
		"""
		Parameters:
			window_lengths [list of positive ints] - a python list containing
					the desired widths of the forward and backward predictors
			weight_exponent [positive float] - the exponent governing the
					sensitivity of the weights to the accuracy of the predictors
					this is 'p' in the original paper
			apriori_f_weights [list of positive floats] - apriori confidence in
					the different forward predictors, 'pi_i' in the paper
			apriori_b_weights [list of positive floats] - apriori confidence in
					the different backward predictors, 'pi_i' in the paper
		Note:
			-window_lengths used for forward and backward prediction are the
			same
			-if apriori weights are given their order is assumed to correspond
			to the order of the window lengths
		"""
        self.window_lengths = window_lengths
        self.weight_exponent = weight_exponent
        self.weight_window = weight_window
        n_predictors = len(window_lengths)

        if apriori_f_weights: self.apriori_f_weights = apriori_f_weights
        else: self.apriori_f_weights = np.ones(n_predictors)/n_predictors

        if apriori_b_weights: self.apriori_b_weights = apriori_b_weights
        else: self.apriori_b_weights = np.ones(n_predictors)/n_predictors


    def predict_forward(self, data, window_width):
        """
        Calculate the forward prediction
		the boundary effects are handled by taking the first preddiction
		equal to the first element and then predicting on a window of increasing
		size until the full window_width is reached
		Parameters:
			data [1D array or list of floats] - the data to be filtered
			window_width [int] - the width of the prediction window
        """
		#first element of output is always the first element of the data
        output = [data[0]]
        for i in range(1,len(data)):
            if i-window_width>=0:
				#full window fits in the data => prediction is the mean of the
				#previous window_width points
                prediction = np.mean(data[i-window_width:i])
            else:
				#window does not fit, prediction is mean of all earlier points
                prediction = np.mean(data[:i])
            output.append(prediction)
        return output

    def predict_backward(self,data,window_width):
        """
        Calculate the backward prediction
		The implementation and parameters are the same as in predict_forward
        """
        output = list()
        len_data = len(data)
        for i in range(len_data-1):
            if i+window_width<len_data:
                prediction = np.mean(data[i+1:i+1+window_width])
            else:
                prediction = np.mean(data[i+1:])
            output.append(prediction)
        output.append(data[-1])
        return output

    def calculate_forward_weights(self, data, predictions):
        """
        Calculate the weights of the forward predictors.
		Parameters:
			data [1D array or list of floats] - the data to be filtered
			predictions [list of 1D arrays] - the predictions to be weighted
        """
        #predictors should be given as lists, if the first element of
		#predictions is not a list it is assumed that only a single forward
		#prediction was given
        if type(predictions[0]) is not list:
            predictions=[predictions]

        len_data = len(data)
        n_predictors = len(predictions)
        #allocate weight array
        f = np.zeros((n_predictors,len_data))

        for i, prediction in enumerate(predictions):
            for k in range(len_data):
                for j in range(self.weight_window):
                    if not k-j<0:
                        f[i,k] += (data[k-j]-prediction[k-j])**2
                #zero should only occur at the beginning, in order to avoid
				#infinities it is replaced by one
                if f[i,k]==0: f[i,k]=1
                f[i,k] = f[i,k]**-self.weight_exponent
            f[i]*=self.apriori_f_weights[i]
        return f

    def calculate_backward_weights(self, data, backward_prediction):
        """
        Calculate the weights of the backward predictors.
		Parameters:
			data [1D array or list of floats] - the data to be filtered
			predictions [list of 1D arrays] - the predictions to be weighted
        """
        #predictors should be given as lists, if the first element of
		#predictions is not a list it is assumed that only a single forward
		#prediction was given
        if type(backward_prediction[0]) is not list:
            backward_prediction=[backward_prediction]

        len_data = len(data)
        n_predictors = len(backward_prediction)
        #allocate weight array
        b = np.zeros((n_predictors,len_data))

        for i, prediction in enumerate(backward_prediction):
            for k in range(len_data):
                for j in range(self.weight_window):
                    if not k+j>=len_data:
                        b[i,k] += (data[k+j]-prediction[k+j])**2
                #zero should only occur at the beginning, in order to avoid
				#infinities it is replaced by one
                if b[i,k]==0: b[i,k]=1
                b[i,k] = b[i,k]**-self.weight_exponent
            b[i]*=self.apriori_b_weights[i]
        return b

    def calculate_prediction(self, data):
        """
        Generate the final prediction of the Chung Kennedy filter
        """
        forward_p = list()
        backward_p = list()

        for window in self.window_lengths:
            forward_p.append(self.predict_forward(data,window))
            backward_p.append(self.predict_backward(data,window))

        forward_w = self.calculate_forward_weights(data, forward_p)
        backward_w = self.calculate_backward_w(data, backward_p)

        sum_weights = np.sum(forward_w,axis=0)+np.sum(backward_w, axis=0)
        forward_w/=sum_weights
        backward_w/=sum_weights

        forward_p = np.asarray(forward_p)
        backward_p = np.asarray(backward_p)

        output = forward_w*forward_p+backward_w*backward_p
        output = np.sum(output, axis=0)
        return output
