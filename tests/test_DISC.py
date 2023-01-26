from copy import copy

import pytest
import numpy as np
import scipy as sp

from src.core.DISC import (
        divisive_segmentation, merge_by_ward_distance,
        compare_IC, compute_emission_matrix,
        empirical_transition_matrix, viterbi_path,
        t_test_changepoint_detection, run_DISC,
        BIC, agglomorative_clustering_fit,
        )
from src.core.DISC.agglomerative_clustering import (Ward_distances,
                                                    merge_states)
from src.core.DISC.divisive_segmentation import (kmeans_assign,
                                                 detect_changepoints)

n_samples = 100
confidence_level = 0.01
crit_val = sp.stats.t.ppf(q=1-confidence_level/2, df=n_samples-1)
noise_sigma = np.sqrt(0.1)
# Edge cases for detecting a CP using t-test are the second and second to last elements because the first and last are excluded in the detection.
CPs_with_edge_cases = [1, 2, 10, 13, 21, 29, 81, 89, 96, 8, 26, 68, 36, 59, 70, 31, 67, 85, 25, 53, 61, 98]
# For idealize_bisect the edge cases need to be excluded because the
# minimum length of each segment is 3.
CPs = [2, 10, 13, 21, 29, 81, 89, 96, 8, 26, 68, 36, 59, 70, 31, 67, 85, 25, 53, 61 ]
multiple_CPs = [(8, 26, 68),
                     (36, 59, 70),
                     (31, 67, 85),
                     (25, 53, 61),
                     (26, 54, 62),
                     ]
too_short_CPs = [0, 1, 98, 99]
multiple_CPs_too_short = [(65, 67)]

def get_states(true_CP):
    return np.concatenate((np.ones(true_CP+1), np.zeros(n_samples-true_CP-1)))

def get_test_data(CPs):
    if type(CPs[0]) == int:
        out = [(cp, get_states(cp)) for cp in CPs]
    else:
        out = []
        for cps in CPs:
            data = np.ones(n_samples)
            for cp in cps:
                data[cp+1:-1] = (data[cp]+1)%2
            data[-1] = data[-2]
            out.append((cps, data))
    return out

@pytest.mark.parametrize("true_CP, data", get_test_data(CPs_with_edge_cases))
def test_t_test_changepoint_detection_no_noise(true_CP, data):
    _, CP = t_test_changepoint_detection(data, noise_sigma)
    assert true_CP==CP

# Test detect_changepoints function.
@pytest.mark.parametrize("true_CP, data", get_test_data(CPs))
def test_detect_changepoints_no_noise_1CP(true_CP, data):
    out, cps = detect_changepoints(data, crit_val, noise_sigma)
    assert np.all(out==data)
    assert np.all(cps==true_CP)

# Test detect_changepoints function.
@pytest.mark.parametrize("true_CP, data", get_test_data(too_short_CPs))
def test_detect_changepoints_no_noise_1CP_too_short(true_CP, data):
    out, cps = detect_changepoints(data, crit_val, noise_sigma)
    assert np.all(out==np.mean(data)*np.ones(n_samples))
    assert cps.size == 0  # I.e. no changepoints found.

@pytest.mark.parametrize("true_CPs, data", get_test_data(multiple_CPs))
def test_detect_changepoints_no_noise_multiple_CPs(true_CPs, data):
    out, cps = detect_changepoints(data, crit_val, noise_sigma)
    assert np.all(cps==true_CPs)
    assert np.all(out==data)

@pytest.mark.parametrize("true_CPs, data", get_test_data(multiple_CPs_too_short))
def test_detect_changepoints_no_noise_multiple_CPs_too_short(true_CPs, data):
    out, cps = detect_changepoints(data, crit_val, noise_sigma)
    assert np.all(out==np.mean(data)*np.ones(n_samples))
    assert cps.size == 0  # I.e. no changepoints found.

@pytest.mark.parametrize("true_CPs, data", get_test_data(multiple_CPs))
def test_kmeans_assign(true_CPs, data):
    centers = [0,1]
    true_counts = [np.sum(data==0), np.sum(data==1)]
    c, out, counts = kmeans_assign(data, centers)
    assert np.all(c==centers)
    assert np.all(out==data)
    assert np.all(counts==true_counts)

@pytest.mark.parametrize("true_CPs, data", get_test_data(multiple_CPs))
def test_compare_BIC_classification_error(true_CPs, data):
    data_fit, _ = detect_changepoints(data, crit_val, noise_sigma)
    data += np.random.randn(np.size(data_fit))  # This is needed to be able to fit a standard deviation when compution the BIC
    data_fit_bad1 = copy(data_fit)
    data_fit_bad1[5] = (data_fit_bad1[5]+1)%2
    data_fit_bad2 = copy(data_fit)
    data_fit_bad2[10] = (data_fit_bad2[10]+1)%2
    ind = compare_IC(data, np.vstack([data_fit, data_fit_bad1, data_fit_bad2]).T, IC="BIC")
    assert ind==0

@pytest.mark.parametrize("true_CPs, data", get_test_data(multiple_CPs))
def test_compare_BIC_too_many_states(true_CPs, data):
    data_fit, _ = detect_changepoints(data, crit_val, noise_sigma)
    data += 0.01*np.random.randn(np.size(data_fit))  # This is needed to be able to fit a standard deviation when compution the BIC
    over_fit = copy(data_fit)
    over_fit[0:true_CPs[0]+1] = 0.99
    too_many_states_fit1 = copy(data_fit)
    too_many_states_fit1[true_CPs[0]+1:true_CPs[1]+1] = 0.01
    too_many_states_fit2 = copy(data_fit)
    too_many_states_fit2[0:true_CPs[0]+1] = 0.9
    too_many_states_fit2[true_CPs[0]+1:true_CPs[1]+1] = 0.1
    ind0 = compare_IC(data, np.vstack([data_fit, over_fit,
                                       too_many_states_fit1,
                                       too_many_states_fit2]).T, IC="BIC")
    ind1 = compare_IC(data, np.vstack([over_fit, data_fit,
                                       too_many_states_fit1,
                                       too_many_states_fit2]).T, IC="BIC")
    ind2 = compare_IC(data, np.vstack([over_fit,
                                       too_many_states_fit1,
                                       data_fit,
                                       too_many_states_fit2,
                                       ]).T, IC="BIC")
    ind3 = compare_IC(data, np.vstack([over_fit,
                                       too_many_states_fit1,
                                       too_many_states_fit2,
                                       data_fit,
                                       ]).T, IC="BIC")
    assert ind0==0
    assert ind1==1
    assert ind2==2
    assert ind3==3

@pytest.mark.parametrize("true_CPs, data", get_test_data(multiple_CPs))
def test_merge_states(true_CPs, data):
    merged = merge_states(data, 0, 1)
    assert np.all(merged == np.mean(data))

@pytest.mark.parametrize("true_CPs, data", get_test_data(multiple_CPs))
def test_merge_by_ward_distance(true_CPs, data):
    data_fit, _ = detect_changepoints(data, crit_val, noise_sigma)
    data += 0.01*np.random.randn(np.size(data_fit))  # This is needed to be able to fit a standard deviation when compution the BIC
    over_fit = copy(data_fit)
    over_fit[0:true_CPs[0]+1] = 0.9
    over_fit[true_CPs[0]+1:true_CPs[1]+1] = 0.1
    all_fits = merge_by_ward_distance(over_fit)
    ind = compare_IC(data, all_fits, IC="BIC")
    assert ind==1
    assert np.shape(all_fits)[1] == len(np.unique(over_fit))

@pytest.mark.parametrize("true_CPs, data", get_test_data(multiple_CPs))
def test_agglomorative_clustering(true_CPs, data):
    data_fit, _ = detect_changepoints(data, crit_val, noise_sigma)
    data += 0.01*np.random.randn(np.size(data_fit))  # This is needed to be able to fit a standard deviation when compution the BIC
    over_fit = copy(data_fit)
    over_fit[0:true_CPs[0]+1] = 0.99
    over_fit[true_CPs[0]+1:true_CPs[1]+1] = 0.01
    ag_fit = agglomorative_clustering_fit(data, over_fit, IC="BIC")
    correct_output = merge_states(over_fit, 0.99, 1)
    correct_output = merge_states(correct_output, 0.01, 0)
    # Check that it finds the correct number of states.
    assert np.all(len(np.unique(ag_fit))==len(np.unique(data_fit)))
    # We need to round the output because otherwise
    # assert 0.004423076923076924 == 0.004423076923076923 (!)
    # might occur.
    assert np.all(np.around(ag_fit, decimals=10)==np.around(correct_output, decimals=10))
