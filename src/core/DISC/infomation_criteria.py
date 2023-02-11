# All credit for the DISC algorithm belongs to the authors of
# White, D.S., Goldschen-Ohm, M.P., Goldsmith, R.H., Chanda, B. Top-down machine learning approach for high-throughput single-molecule analysis. Elife 2020, 9
# The code in this module is based on their paper and partly on their
# matlab implementation at commit af19eae on https://github.com/ChandaLab/DISC/

import numpy as np
from scipy.stats import norm

from .utils import normal_pdf

def BIC_full(data, data_fit):
    """
    Computes the Bayesian Information Criterion (BIC) of the model that
    produced the fit in `data_fit`.
    Input:
        data - N×1 array containing the original observations
        data_fit - N×1 array containing an idealization fit of the data
    Output:
        float - value of the Bayesian Information Criterion for the model
                that produced data_fit
          OR negative infinity if `data` and `data_fit` are identical
    """
    if np.any(data!=data_fit):
        n_states = len(set(data_fit))
        N = len(data)
        n_cps = len(np.where(np.diff(data_fit)!=0)[0])
        BIC = (n_cps+n_states)*np.log(N)
        means = np.unique(data_fit)
        K = len(means)
        stds = np.zeros(K)
        pis = np.zeros(K)  # mixture coefficients
        for (i,m) in enumerate(means):
            stds[i] = norm.fit(data[data_fit==m])[1]
            pis[i] = np.sum(data_fit==m)
        pis /= N
        for x in data:
            L = 0
            for (j,m) in enumerate(means):
                L += pis[j]*normal_pdf(x, mu=m, sigma=stds[j])
            BIC -= 2*np.log(L)
    else:
        BIC = -1*np.infty
    return BIC

def BIC_approx(data, data_fit):
    """
    Computes the Bayesian Information Criterion (BIC) of the model that
    produced the fit in `data_fit`.
    This implementation differs from the one I would derive from the formula
    given in the paper, it is however how it is implemented in the matlab code
    by the DISC authors.
    Input:
        data - N×1 array containing the original observations
        data_fit - N×1 array containing an idealization fit of the data
    Output:
        float - value of the Bayesian Information Criterion for the model
                that produced data_fit
          OR negative infinity if `data` and `data_fit` are identical
    """
    if np.any(data!=data_fit):
        n_states = len(set(data_fit))
        N = len(data)
        n_cps = len(np.where(np.diff(data_fit)!=0)[0])
        BIC = (n_cps+n_states)*np.log(N)
        BIC += N*np.log( np.sum((data-data_fit)**2/N) )
    else:
        BIC = -1*np.infty
    return BIC

def BIC(data, data_fit, BIC_method="approx"):
    if BIC_method=="approx":
        return BIC_approx(data, data_fit)
    elif BIC_method=="full":
        return BIC_full(data, data_fit)

def compare_IC(data, fits, IC="BIC", BIC_method="approx"):
    """
    Determine whether `fit_1` or `fit_2` is a better fit for the data
    contained in `data` based on an Information Criterion (IC).
    -- For the time being the IC used will be the Bayesian Information
       Criterion. This primarily a function to allow for easier
       implementation of other ICs in the future.
    Input:
        data - N×1 array containing the original observations
        fits - N×k array containing k fits to the data
        IC - String specifying the IC to be used
             - "BIC" for Bayesian Information Criterion
    Output:
        integer - index of the fit with the lowest IC value
    """
    IC_vals = np.zeros(np.shape(fits)[1])
    if IC == "BIC":
        for (i,f) in enumerate(fits.T):
            IC_vals[i] = BIC(data, f, BIC_method=BIC_method)
    else:
        raise Exception(f"Unknown information criterion: {IC}")
    return np.argmin(IC_vals)
