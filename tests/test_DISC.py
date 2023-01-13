import pytest
import numpy as np
import scipy as sp

from src.core.DISC.divisive_segmentation import detect_changepoints
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
true_CPs_with_edge_cases = [1, 2, 10, 13, 21, 29, 81, 89, 96, 8, 26, 68, 36, 59, 70, 31, 67, 85, 25, 53, 61, 98]
# For idealize_bisect the edge cases need to be excluded because the
# minimum length of each segment is 3.
true_CPs = [2, 10, 13, 21, 29, 81, 89, 96, 8, 26, 68, 36, 59, 70, 31, 67, 85, 25, 53, 61 ]
true_multiple_CPs = [(8, 26, 68),
                     (36, 59, 70),
                     (31, 67, 85),
                     (25, 53, 61),
                     (26, 54, 62),
                     ]
true_too_short_CPs = [0, 1, 98, 99]

@pytest.mark.parametrize("true_CP", true_CPs_with_edge_cases)
def test_t_test_changepoint_detection_no_noise(true_CP):
    states = np.concatenate((np.ones(true_CP+1),
                             np.zeros(n_samples-true_CP-1)))
    _, CP = t_test_changepoint_detection(states, noise_sigma)
    assert true_CP==CP

# Test detect_changepoints function.
@pytest.mark.parametrize("true_CP", true_CPs)
def test_detect_changepoints_no_noise_1CP(true_CP):
    states = np.concatenate((np.ones(true_CP+1),
                             np.zeros(n_samples-true_CP-1)))
    out, cps = detect_changepoints(states, crit_val, noise_sigma)
    assert np.all(out==states)
    assert np.all(cps==true_CP)

# Test detect_changepoints function.
@pytest.mark.parametrize("true_CP", true_too_short_CPs)
def test_detect_changepoints_no_noise_1CP_too_short(true_CP):
    states = np.concatenate((np.ones(true_CP+1),
                             np.zeros(n_samples-true_CP-1)))
    out, cps = detect_changepoints(states, crit_val, noise_sigma)
    assert np.all(out==np.mean(states)*np.ones(n_samples))
    assert cps.size == 0  # I.e. no changepoints found.

@pytest.mark.parametrize("true_CPs", true_multiple_CPs)
def test_detect_changepoints_no_noise_multiple_CPs(true_CPs):
    states = np.concatenate((np.ones(true_CPs[0]+1),
                             np.zeros(true_CPs[1]-true_CPs[0]),
                             np.ones(true_CPs[2]-true_CPs[1]),
                             np.zeros(n_samples-true_CPs[2]))
                            )
    out, cps = detect_changepoints(states, crit_val, noise_sigma)
    assert np.all(cps==true_CPs)
    assert np.all(out==states)

