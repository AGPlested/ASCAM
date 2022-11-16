import numpy as np

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
