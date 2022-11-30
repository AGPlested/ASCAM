import numpy as np

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
