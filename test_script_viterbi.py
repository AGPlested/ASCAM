n_states = 4
n_samples = 10000
noise_sigma = np.sqrt(0.1)
true_path = np.random.randint(low=0, high=n_states, size=n_samples)
noise = noise_sigma*np.random.randn(n_samples)
obs = true_path + noise
initial_dist = np.ones(n_states)/n_states
components = np.array([initial_dist,
                       np.array([i for i in range(n_states)]),
                       noise_sigma*np.ones(n_states)]).T
EM = compute_emission_matrix(obs, components)
TM = empirical_transition_matrix(true_path, n_states)

import timeit

def vp():
    return viterbi_path(initial_dist, TM, EM)
def vpnp():
    return viterbi_path_np(initial_dist, TM, EM)

n_runs = 10
timeit.timeit(vp, number=n_runs)/n_runs
timeit.timeit(vpnp, number=n_runs)/n_runs

p=vp()
pnp=vpnp()
print(np.sum(p!=pnp))
print(p)
print(pnp)
print(true_path)

