#import logging
import numpy as np


def apply_filter(signal, window):
    """Apply filter window to a signal.

	for now datatype should be using numpy types such as 'np.int16'
	the entire file is read assuming datatype so header length should
	be specified in words of the same bit length
	filter_frequency should be supplied in units of sampling rate
	filter_type does not need to be set until/unless we start using
	other filters
	method allows for using scipy fft convolve which might be faster
	for large signal sets"""

    # pad with constant values to reduce boundary effects and keep
    # original length of array
    padLength = int((len(window) - 1) / 2)  # `len(window)` is always odd
    leftPad = np.ones(padLength) * signal[0]
    rightPad = np.ones(padLength) * signal[-1]
    signal = signal.flatten()
    signal = np.hstack((leftPad, signal, rightPad))
    output = np.convolve(signal, window, mode="valid")
    return output


def gaussian_window(filter_frequency, sampling_rate=4e4):
    """This calculates the coefficients for a disrete Gaussian filter
	as described in equation A10 in chapter 19 in the blue book
	Parameters:
		filter_frequency - should be given in units Hz
		sampling_rate - units of Hz"""

    filter_frequency /= sampling_rate
    sigma = 0.1325 / filter_frequency

    if sigma >= 0.62:  # filter as normal
        n = int(4 * sigma)
        non_neg_ind_coefficients = np.zeros(n + 1)
        for index in range(n + 1):
            non_neg_ind_coefficients[index] = (
                1
                / (np.sqrt(2 * np.pi) * sigma)
                * np.exp(-index ** 2 / (2 * sigma ** 2))
            )
            negative_ind_coeff = non_neg_ind_coefficients[:0:-1]
        coefficients = np.hstack((negative_ind_coeff, non_neg_ind_coefficients))
    else:  # light filtering as described in blue book
        coefficients = np.zeros(3)
        coefficients[0] = sigma * sigma / 2
        coefficients[1] = 1 - 2 * coefficients[0]
        coefficients[2] = coefficients[0]

    return coefficients


def gaussian_filter(signal, filter_frequency, sampling_rate=4e4):
    window = gaussian_window(filter_frequency, sampling_rate)
    output = apply_filter(signal, window)
    return output


class ChungKennedyFilter:
    """Create a "Chung-Kennedy" filter as described in
	https://doi.org/10.1016/0165-0270(91)90118-J"""

    def __init__(
        self,
        window_lengths,
        weight_exponent,
        weight_window,
        apriori_f_weights=False,
        apriori_b_weights=False,
        boundary_mode="increasing",
    ):
        """Chung-Kennedy filter.

            Parameters:
            window_lengths [list of positive ints] - a list containing the
                desired widths of the forward and backward predictors

            weight_exponent [positive float] - the exponent governing the
                sensitivity of the weights to the accuracy of the predictors
                this is 'p' in the original paper

            apriori_f_weights [list of positive floats] - apriori confidence in
                the different forward predictors, 'pi_i' in the paper

            apriori_b_weights [list of positive floats] - apriori confidence in
                the different backward predictors, 'pi_i' in the paper

            boundary_mode [string] - how to deal with boundary effects either
                'increasing' which will calculate predictions with increasing
                window widths or 'padded' which will pad the signal with 0s
                at the edges

        Note:
            -window_lengths used for forward and backward prediction are the
            same
            -if apriori weights are given their order is assumed to correspond
            to the order of the window lengths"""

        self.window_lengths = window_lengths
        self.weight_exponent = weight_exponent
        self.weight_window = weight_window
        self.mode = boundary_mode

        n_predictors = len(window_lengths)

        if apriori_f_weights:
            self.apriori_f_weights = apriori_f_weights
        else:
            self.apriori_f_weights = np.ones(n_predictors) / n_predictors

        if apriori_b_weights:
            self.apriori_b_weights = apriori_b_weights
        else:
            self.apriori_b_weights = np.ones(n_predictors) / n_predictors

    def predict_forward(self, data, window_width):
        """Calculate the forward prediction

		the boundary effects are handled by taking the first prediction
		equal to the first element and then predicting on a window of increasing
		size until the full window_width is reached
		Parameters:
			data [1D array] - data for with the forward prediction is to be
							  calculated
			window_width [int] - number of points to take into consideration
								 when predicting
		Returns:
			forward_prediction [1D array] - forward prediciton of the data"""

        forward_prediction = np.zeros(len(data))
        if self.mode == "increasing":
            # take first prediction equal to real value
            forward_prediction[0] = data[0]
            # add points with offsets -1,...,-window_width
            for i in range(1, window_width + 1):
                forward_prediction[i:] += data[:-i]
            # take average of values to get prediction
            for i in range(window_width):
                forward_prediction[i] /= i + 1
            forward_prediction[window_width:] /= window_width
        elif self.mode == "padded":
            data = np.hstack((np.zeros(window_width), data))
            for i in range(1, window_width + 1):
                forward_prediction += data[window_width - i : -i]
            forward_prediction /= window_width
        else:
            raise ValueError(
                f"Mode {self.mode} is an unknown method for dealing\
								with edges"
            )
        return forward_prediction

    def predict_backward(self, data, window_width):
        """Calculate the backward prediction based on the mean of next
		#window_width data points
		The boundary (end of array) is dealt with by taking the last prediction
		equal to the original datapoint and then predicting for a window of
		increasing size until #window_width is reached
		Parameters:
			data [1D array] - data for with the backward prediction is to be
							  calculated
			window_width [int] - number of points to take into consideration
								 when predicting
		Returns:
			backward_prediction [1D array] - backward prediction of the data"""

        len_data = len(data)
        backward_prediction = np.zeros(len_data)
        if self.mode == "increasing":
            # since we cannot backward predict the last element we set it equal
            # to the original datapoint
            backward_prediction[-1] = data[-1]
            # add to each point in the prediction the original data with offset
            # 1,...,window_width
            for i in range(1, window_width):
                backward_prediction[:-i] += data[i:]
            # take the means of all the points in prediction
            for i in range(1, window_width):
                backward_prediction[-i] /= i
            backward_prediction[: len_data - window_width + 1] /= window_width
        elif self.mode == "padded":
            data = np.hstack((data, np.zeros(window_width)))
            for i in range(1, window_width + 1):
                backward_prediction += data[i : len(data) - window_width + i]
            backward_prediction /= window_width
        else:
            raise ValueError(
                f"Mode {self.mode} is an unknown method for dealing\
                with edges"
            )
        return backward_prediction

    def calculate_forward_weights(self, data, predictions):
        """Calculate the weights of the backward predictors.

		Where the window for calculating the weights is larger than the
		available number of datapoints all those that are present are used.
		Any 0 differences will be replaced by 1 (this is arbitrary)
		Parameters:
			data [1D array or list of floats] - the data to be filtered
			predictions [2D array or list of 1D arrays] - the predictions to be
											weighted n_prediction by len_data
		Returns:
			forward_w [2D array] - array containng the weights for the different
								predictors in the rows, n_prediction by len_data
		"""

        # predictors should be given as lists, if the first element of
        # predictions is not a list it is assumed that only a single forward
        # prediction was given
        if type(predictions[0]) is not np.ndarray:
            predictions = [predictions]

        len_data = len(data)
        n_predictors = len(predictions)
        # allocate weight array
        forward_w = np.zeros((n_predictors, len_data))
        for i, prediction in enumerate(predictions):
            diff = (data - prediction) ** 2
            forward_w[i] = diff
            # add the differenes for each offset
            for j in range(1, self.weight_window):
                # since we cannot slice with negative values without getting
                # elements from the end of the array we have to seperate cases
                for k in range(self.weight_window):
                    # if we do not have the full window available we use those
                    # that are present
                    if not k - j < 0:
                        forward_w[i, k] += diff[k - j]
                # everywhere else the window fits and we can simply use array
                # arithmetic
                forward_w[i, self.weight_window :] += diff[self.weight_window - j : -j]
            # in order to avoid infinities from tiny numers we considering
            # everyhing <e-20 as 0 when applying weight exponent
            # the corresponding weights are set to 1 befre applying the exponent
            # in order make them relatively insignificant later on
            # (this is based on the assumption that such an exact match between
            # prediction and data is an artefact of the 'increasing' method and
            # should therefore be discounted)
            forward_w[i, np.where(forward_w[i] < 1e-20)] = 1
            forward_w[i] = forward_w[i] ** -self.weight_exponent
            forward_w[i] *= self.apriori_f_weights[i]
        return forward_w

    def calculate_backward_weights(self, data, predictions):
        """Calculate the weights of the backward predictors.

		Where the window for calculating the weights is larger than the
		available number of datapoints all those that are present are used.
		Any 0 differences will be replaced by 1 (this is arbitrary)
		Parameters:
			data [1D array or list of floats] - the data to be filtered
			predictions [2D array or list of 1D arrays] - the predictions to be
											weighted n_prediction by len_data
		Returns:
			forward_w [2D array] - array containng the weights for the different
								predictors in the rows, n_prediction by len_data
		"""

        # if the first element/row of predictions is not an array it is assumed
        # that only one prediction was given and we turn it into a list so the
        # rest of the code will run
        if type(predictions[0]) is not np.ndarray:
            predictions = [predictions]

        len_data = len(data)
        n_predictors = len(predictions)
        # allocate weight array
        b = np.zeros((n_predictors, len_data))

        for i, prediction in enumerate(predictions):
            diff = (data - prediction) ** 2
            # each weight depend on the accuracy at its timepoint
            b[i] = diff
            # add to each timepoint the differences again with an offset
            # slicing numpy arrays up to larger index than length of the array
            # simply return up to the last element
            for j in range(1, self.weight_window):
                b[i, :-j] += diff[j : len_data + j]
            b[i, np.where(b[i] < 1e-20)] = 1
            b[i] = b[i] ** -self.weight_exponent
            b[i] *= self.apriori_b_weights[i]
        return b

    def apply_filter(self, data):
        """Apply the Chung Kennedy filter to the given data.

		Parameters:
			data [1D array] - data to be filtere
		Returns:
			filtered [1D array] - the filtered version of the data"""

        n_predictors = len(self.window_lengths)
        len_data = len(data)
        forward_p = np.zeros((n_predictors, len_data))
        backward_p = np.zeros((n_predictors, len_data))

        for i, window in enumerate(self.window_lengths):
            forward_p[i] = self.predict_forward(data, window)
            backward_p[i] = self.predict_backward(data, window)

        forward_w = self.calculate_forward_weights(data, forward_p)
        backward_w = self.calculate_backward_weights(data, backward_p)

        # normalize the weights to sum to one by dividing by the sum
        sum_weights = np.sum(forward_w, axis=0) + np.sum(backward_w, axis=0)
        forward_w /= sum_weights
        backward_w /= sum_weights

        filtered = forward_w * forward_p + backward_w * backward_p
        filtered = np.sum(filtered, axis=0)
        return filtered
