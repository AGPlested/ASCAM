# All credit for the DISC algortihm belongs to the authors of
# White, D.S., Goldschen-Ohm, M.P., Goldsmith, R.H., Chanda, B. Top-down machine learning approach for high-throughput single-molecule analysis. Elife 2020, 9
# The code in this module is based on their paper and partly on their
# matlab implementation at commit af19eae on https://github.com/ChandaLab/DISC/

from copy import copy

import numpy as np

from .infomation_criteria import compare_IC

def Ward_distances(data_fit):
    """
    Computes the Ward distance between all the states found in `data_fit`.
    Assumes data_fit has been idealized to a small number of states.
    Input:
        data - N×1 array containing an idealization
    Output:
        K×K upper triangular matrix containing the pairwise Ward distances
    """
    states = np.unique(data_fit)
    K = len(states)
    n = np.zeros(K)
    for (i,s) in enumerate(states):
        n[i] = np.sum(data_fit==s)
    ward_d = np.zeros((K,K))
    for i in range(K):
        for j in range(i+1, K):
            ward_d[i,j] = (np.sqrt( 2*n[i]*n[j]/(n[i]+n[j]) )
                           * np.sqrt((states[i]-states[j])**2)
                           )
    return ward_d

def merge_by_ward_distance(data_fit):
    """
    Given an idealization of the data into K states recursively merge the
    two states which are closest in Ward distance and return all the
    resulting fits.
    When two states are merged the amplitude of the new state is the
    average of the amplitudes of the two original states weighted by the
    number of observations assigned to each respectively.
    Input:
        data - N×1 array containing an idealization
    Output:
        N×K array containing the idealizations obtained
    """
    N = len(data_fit)
    centers = np.unique(data_fit)
    n_centers = len(centers)
    fit_index = n_centers-1
    all_data_fits = np.zeros((N, n_centers))
    all_data_fits[:, -1] = data_fit
    while fit_index > 0:
        data_fit = all_data_fits[:, fit_index]
        centers = np.unique(data_fit)
        # fit clusters with minimum Ward distance between them
        ward_d = Ward_distances(data_fit)
        i, j = np.where( ward_d==np.min(ward_d[np.nonzero(ward_d)]) )
        # create new fit
        new_center = np.mean(
                np.concatenate([data_fit[data_fit==centers[i]],
                                data_fit[data_fit==centers[j]]])
                             )
        new_data_fit = copy(data_fit)
        # find indices of clusters to be merged
        new_c_ind = np.concatenate([np.where(data_fit==centers[i]),
                                    np.where(data_fit==centers[j])],
                                   axis=1
                                   ).flatten()
        new_data_fit[new_c_ind] = new_center
        fit_index -= 1
        all_data_fits[:,fit_index] = new_data_fit
    return all_data_fits

def agglomorative_clustering_fit(data, data_fit, IC="BIC"):
    """
    Determine whether the idealization in `data_fit` can be improved by
    recursively merging states that are closest in Ward distance and
    return the idealization with the best fit to `data` as measured by
    the given information criterion (`IC`).
    Input:
        data - N×1 array containing observations
        data_fit - N×1 array containing an idealization of `data`
        IC - string indicating which information criterion to use to
             evaluate the quality of the fit.
    Output:
        N×1 array containing the best fit as measured by `IC`
    """
    all_data_fits = merge_by_ward_distance(data_fit)
    best_fit_ind = compare_IC(data, all_data_fits, IC=IC)
    return all_data_fits[:, best_fit_ind]
