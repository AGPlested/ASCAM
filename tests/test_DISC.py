import pytest
import numpy as np
import scipy as sp

from src.core.DISC.divisive_segmentation import (kmeans_assign,
                                                 detect_changepoints)
from src.core.DISC import (
        divisive_segmentation, merge_by_ward_distance,
        compare_IC, compute_emission_matrix,
        empirical_transition_matrix, viterbi_path,
        t_test_changepoint_detection, run_DISC,
        )

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
