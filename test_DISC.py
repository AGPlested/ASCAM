import matplotlib.pyplot as plt
import numpy as np
import scipy as sp

from src.core.DISC.divisive_segmentation import idealize_bisect
from src.core.DISC import (
        divisive_segmentation, merge_by_ward_distance,
        compare_IC, compute_emission_matrix,
        empirical_transition_matrix, viterbi_path,
        t_test_changepoint_detection, run_DISC,
        )

# Test detection of a single changepoint by means of student's t-test.
n_samples = 100
true_CP = 10
print(f"True changepoint is at {true_CP}.")
n_states = 2
noise_sigma = np.sqrt(0.1)
states = np.concatenate((np.ones(true_CP+1),
                         np.zeros(n_samples-true_CP-1)))
noise = noise_sigma*np.random.randn(n_samples)
data = states + noise
T, CP = t_test_changepoint_detection(states, noise_sigma)
print(f"Found changepoint at {CP}.")

# Test idealize_bisect function.
confidence_level = 0.001
crit_val = sp.stats.t.ppf(q=1-confidence_level/2, df=n_samples-1)
out = idealize_bisect(data, crit_val, noise_sigma)


def generate_data(N = 10000,
                  n_states=5,
                  lseg = [10, 1000],
                  noise_sigma = np.sqrt(0.1), ):
    n = 0  # Index in generated data.
    data = np.zeros(N)  # Holds the "observed" data, i.e. including noise.
    truth = np.zeros(N)  # Holds the underlying sequence of states.
    while n < N:
        state = np.random.randint(n_states)
        l = np.random.randint(*lseg)
        if l > N-n:
            l = N-n
            noise = noise_sigma*np.random.randn(l)
            data[n:N] = state*np.ones(l) + noise
            truth[n:N] = state
            break
        else:
            noise = noise_sigma*np.random.randn(l)
            data[n:n+l] = state*np.ones(l) + noise
            truth[n:n+l] = state
            n+=l
    return truth, data

# Test divisive segmentation.
truth, data = generate_data(N=10000, lseg=[10,100])
ds_fit, n_found_states = divisive_segmentation(data, confidence_level=0.01, min_cluster_size=10)
plt.plot(data, label="data")
plt.plot(truth, label="truth")
plt.plot(ds_fit, label="fit", alpha=0.5)
plt.show()

N = 1000
lseg = [10,100]
n_states = 5
truth, data = generate_data(N, n_states, lseg)
fit = run_DISC(data)
plt.plot(data, label="data")
plt.plot(truth, label="truth")
plt.plot(fit, label="fit", alpha=0.5)
plt.show()
