import numpy as np
import scipy as sp

# It looks like the t-test could be computed in a vectorized manner
# for all point in parallel.
def t_test_changepoint_detection(data, noise_std):
    """
        Input :
            data = 1×N array of data in which to look for a change point
            noise_std = estimated standard deviation of the data
    """
    N = len(data)
    T = 0  # highest value of t-statistic
    CP = None # index of current changepoint
    # Speed up T-Test computations by computing all sums only once
    cum_sum = np.cumsum(data)
    total_sum = cum_sum[-1]
    # Drop first and last data points from the loop as in the original
    # author's code.
    for n in range(2,N-1):
        mu_1 = cum_sum[n] / n
        mu_2 = (total_sum - cum_sum[n]) / (N-n)
        t = abs((mu_2 - mu_1)) / noise_std / np.sqrt(1/n+1/(N-n))
        if t > T:
            T = t      # best T value so far
            CP = n     # Location of best T value
    return T, CP

def detect_changpoints(data, critical_value, noise_std):
    # Find bisecting changepoint using t-test.
    t, cp = t_test_changepoint_detection(data, noise_std)
    # If t-statistic is significant bisect data at changepoint and
    # recursively look for changepoints in the resulting segments.
    if t >= critical_value:
        first_segment = detect_changpoints(data[:cp+1], critical_value,
                                           noise_std)
        second_segment = detect_changpoints(data[cp+1:], critical_value,
                                           noise_std)
        out = np.concatenate((first_segment, second_segment))
    else:  # If t is not significant return data idealized to mean value.
        out = np.mean(data) * np.ones(len(data))
    return out

# def changepoint_detection(data, confidence_level):
#     """
#         Input :
#             data = 1×N array of data in which to look for a change point
#             confidence_level = float ∈(0,1), confidence value for t-test
#     """
#     N = len(data)
#     crit_val = sp.stats.t.ppf(q=1-confidence_level/2, df=N-1)
#     # Estimate standard deviation of noise in data.
#     # Based on the DISC code, they reference:
#     # Shuang et al., J. Phys Chem Letters, 2014, DOI: 10.1021/jz501435p.
#     sorted_wavelet = np.sort(abs(np.diff(data) / 1.4))
#     noise_std = sorted_wavelet[round(0.682 * (N-1))]
