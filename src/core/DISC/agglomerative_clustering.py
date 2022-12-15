from copy import copy

import numpy as np

def Ward_distances(data):
    """
    Computes the Ward distance between all the states found in `data`.
    Assumes data has been idealized to a small number of states.
    """
    states = np.unique(data)
    K = len(states)
    n = np.zeros(K)
    for (i,s) in enumerate(states):
        n[i] = np.sum(data==s)
    ward_d = np.zeros((K,K))
    for i in range(K):
        for j in range(i+1, K):
            ward_d[i,j] = (np.sqrt( 2*n[i]*n[j]/(n[i]+n[j]) )
                           * np.sqrt(states[i]**2+states[j]**2)
                           )
    return ward_d

def merge_by_ward_distance(data_fit):
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
        new_center = np.mean(np.concatenate([data_fit[data_fit==centers[i]],
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
    all_data_fits = merge_by_ward_distance(data_fit)
    best_fit_ind = compare_IC(data, all_data_fits, IC=IC)
    return all_data_fits[:, best_fit_ind]
