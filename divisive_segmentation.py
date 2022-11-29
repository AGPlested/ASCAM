import numpy as np
import scipy as sp
from scipy.cluster.vq import kmeans

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

def detect_changpoints(data, critical_value, noise_std, min_seg_length=3):
    id_bisect = idealize_bisect(data, critical_value, noise_std,
                           min_seg_length)
    cps = np.where(np.diff(id_bisect)!=0)[0]
    return id_bisect, cps

def idealize_bisect(data, critical_value, noise_std, min_seg_length=3):
    # Find bisecting changepoint using t-test.
    t, cp = t_test_changepoint_detection(data, noise_std)
    # If t-statistic is significant bisect data at changepoint and
    # recursively look for changepoints in the resulting segments.
    if cp is not None and t >= critical_value and len(data) >= min_seg_length:
        first_segment = idealize_bisect(data[:cp+1], critical_value,
                                           noise_std)
        second_segment = idealize_bisect(data[cp+1:], critical_value,
                                           noise_std)
        out = np.concatenate((first_segment, second_segment))
    else:  # If t is not significant return data idealized to mean value.
        out = np.mean(data) * np.ones(len(data))
    return out

def changepoint_detection(data, confidence_level, min_seg_length=3):
    """
        Input:
            data = 1×N array of data in which to look for a change point
            confidence_level = float ∈(0,1), confidence value for t-test
        Output:
            id_bisect = 1×N array containing the idealization of the data
                        achieved by recursive changepoint detection and
                        setting the discovered segments equal to their mean
            cps = 1×C array containing the indices of the changepoints,
                  where C is the number of changepoints
    """
    N = len(data)
    crit_val = sp.stats.t.ppf(q=1-confidence_level/2, df=N-1)
    # Estimate standard deviation of noise in data.
    # Based on the DISC code, they reference:
    # Shuang et al., J. Phys Chem Letters, 2014, DOI: 10.1021/jz501435p.
    sorted_wavelet = np.sort(abs(np.diff(data) / 1.4))
    noise_std = sorted_wavelet[round(0.682 * (N-1))]
    id_bisect, cps = detect_changpoints(data, critical_value=crit_val,
                                        noise_std=noise_std,
                                        min_seg_length=min_seg_length)
    return id_bisect, cps

def BIC(data, data_fit):
    """
    Computes the Bayesion Information Criterion (BIC) of the model that
    produced the fit in `data_fit`.
    Note: I believe there are some important factors missing from the
      computation below, however this is how it is implmented in the
      original version of DISC, so we will use this for now.
    """
    n_states = len(set(data_fit))
    N = len(data)
    n_cps = len(np.where(np.diff(data_fit)!=0)[0])
    BIC = (n_cps+n_states)*np.log(N)
    if np.any(data!=data_fit):
        BIC += N*np.log( np.sum((data-data_fit)**2/N) )
    return BIC

def compare_IC(data, fit_1, fit_2, IC="BIC"):
    """
    Determine whether `fit_1` or `fit_2` is a better fit for the data
    contained in `data` based on an Information Criterion (IC).
    -- For the time being the IC used will be the Bayesion Information
       Criterion. This primarily a function to allow for easier
       implementation of other ICs in the future.
    Input:
        data - N×1 array containing the original observations
        fit_1 - N×1 array containing a fit
        fit_2 - N×1 array containing a fit
        IC - String specifying the IC to be used
              - "BIC" for Bayesion Information Criterion
    Output:
        integer - 1 if `fit_1` is better or both are equal, 2 if `fit_2`
                  is better
    """
    if IC == "BIC":
        IC_1 = BIC(data, fit_1)
        IC_2 = BIC(data, fit_2)
    else:
        raise Exception(f"Unknown information criterion specified: {IC}")
    if IC_1 <= IC_2:
        return 1
    else:
        return 2

def kmeans_assign(data, center_guesses, *args, **kwargs):
    """
    Perform k-means clutering using the scipy kmeans function on the
    input data and return the centers and an array with each index
    assigned to the closest center. Also return an array with the numbers
    of elements assigned to each center.
    """
    centers, _ = kmeans(data, center_guesses, *args, **kwargs)
    # get distances between data points and centers in N×#centers array
    dists = np.abs(data[:, np.newaxis] - centers[np.newaxis, :])
    # find the center closts to each data point
    inds = np.argmin(dists, axis=1)
    counts = np.zeros(len(centers))
    # assign value of closest center to each data point
    assigned = np.zeros(len(data))
    for (k, c) in enumerate(centers):
        assigned[inds==k] = c
        counts[k] = np.sum(inds==k)
    return centers, assigned, counts

