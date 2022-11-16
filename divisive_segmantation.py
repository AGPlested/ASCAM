import numpy as np

def tTestCP(data, noise_std):
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
    # main loop
    # Drop first and last data points from the loop
    # (can't compute a mean with only 1 data point)
    for n in range(2,N-1):
        # compute mean of segment 1 assuming CP at k mean(data(1:CP))
        mu_1 = cum_sum[n] / n
        # compute mean of segment 2 assuming CP at k mean(data(1+CP:end))
        mu_2 = (total_sum - cum_sum[n]) / (N-n)
        # compute t-value
        t = abs((mu_2 - mu_1)) / noise_std / np.sqrt(1/n+1/(N-n))
        # is the new t value better than the current best T value?
        if t > T:
            T = t      # best T value so far
            CP = n     # Location of best T value
    return T, CP
