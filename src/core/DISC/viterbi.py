from copy import copy
import matplotlib.pyplot as plt
import numpy as np

# Assuming the states are 1-dimensional. This will be true in practice.
def normal_pdf(x, mu=0, sigma=1):
    return np.exp(-0.5 * ((x-mu)/sigma)**2) / (np.sqrt(2*np.pi) * sigma)

def compute_emission_matrix(observations, components):
    """
    Compute the probability of each observation being generated by each
    state.
    Input:
     observations = N×1 array
     components = K×3 array
    N = Length of observations
    K = Number of states
    """
    n_obs = len(observations)
    n_states = np.shape(components)[1]
    emission_matrix = np.zeros((n_states, n_obs))
    for i in range(n_states):
        mu = components[1,i]
        sigma = components[2,i]
        emission_matrix[i,:] = normal_pdf(observations, mu=mu, sigma=sigma)
    # Return the normalized matrix
    return emission_matrix/np.sum(emission_matrix, axis=1, keepdims=True)

def empirical_transition_matrix(data_fit):
    """
    Compute the transition matrix of a Markov chain based on a
    realization thereof.
    Input:
     data_fit = fit sorting the data into a small number of states
    N = Length of sample
    K = Number of states
    """
    states = np.unique(data_fit)
    n_states = len(states)
    # Convert data_fit into a trajectory in which the states are
    # represented by integers.
    trajectory = copy(data_fit)
    for (i,s) in enumerate(states):
        trajectory[data_fit==s] = i
    transition_matrix = np.zeros((n_states, n_states))
    trajectory = trajectory.astype(int)
    for i in range(len(trajectory)-1):
        transition_matrix[trajectory[i], trajectory[i+1]] += 1
    # If any states are never exited add small noise to the matrix to avoid
    # diving by zero.
    if np.any(np.sum(transition_matrix, axis=1)==0):
        transition_matrix += 1e-6
    # Return the normalized matrix
    return transition_matrix/np.sum(transition_matrix, axis=1,
                                    keepdims=True)

# Old, less vectorized implementation of Viterbi algorithm.
# Left here for now because it's more readable and might be helpful with
# debugging.
# def viterbi_path(initial_dist, transition_matrix,
#                  emission_matrix):
#     (K,N) = np.shape(emission_matrix)
#     # probability of data point belonging to each state
#     state_prob = np.zeros((K,N))
#     # State assignment of each data point per state
#     predecessor = np.zeros((K,N), dtype=int)
#     # scale = np.zeros(1,N)  # 1 / total probabilities of all states
#     # the `scale` matrix can be used to calculate the log likelihood of
#     # the viterbi path
#     # Initalization: Determine the most likely state of data point 0
#     state_prob[:,0] = initial_dist * emission_matrix[:,0]
#     # scale[0] = 0/sum(state_prob[:,0]);
#     # normalize values to sum to 1
#     state_prob[:,0] = state_prob[:,0] / np.sum(state_prob[:,0])
#     # Set predecessor of initial state to arbitrary value, since there is
#     # no predecessor to n=0
#     predecessor[:,0] = 0
#     # Forward Loop for data point 2 to end:
#     for n in range(1,N):
#         for k in range(K):
#             A = state_prob[:, n-1] * transition_matrix[:,k]
#             predecessor[k, n] = np.argmax(A)
#             state_prob[k, n] = A[predecessor[k, n]]
#             state_prob[k, n] = state_prob[k ,n] * emission_matrix[k, n]
#         # scale[n] = 1/sum(state_prob[:,n]);
#         # normalize
#         state_prob[:, n] = state_prob[:,n] / np.sum(state_prob[:,n])
#     # Find Most probable state path
#     path = np.zeros(N, dtype=int)
#     # loop backwards from data points N-1 to end
#     path[-1] = np.argmax(state_prob[:,-1])  # Last data point
#     for n in range(N-2,-1,-1):
#         path[n] = predecessor[path[n+1],n+1];
#     # log_likelihood = -sum(log(scale));
#     return path

def viterbi_path(initial_dist, transition_matrix,
                 emission_matrix, state_vals=None):
    (K,N) = np.shape(emission_matrix)
    # probability of data point belonging to each state
    state_prob = np.zeros((K,N))
    # State assignment of each data point per state
    predecessor = np.zeros((K,N), dtype=int)
    # scale = np.zeros(1,N)  # 1 / total probabilities of all states
    # the `scale` matrix can be used to calculate the log likelihood of
    # the viterbi path
    # Initalization: Determine the most likely state of data point 0
    state_prob[:,0] = initial_dist * emission_matrix[:,0]
    # scale[0] = 0/sum(state_prob[:,0]);
    # normalize values to sum to 1
    state_prob[:,0] = state_prob[:,0] / np.sum(state_prob[:,0])
    # Set predecessor of initial state to arbitrary value, since there is
    # no predecessor to n=0
    predecessor[:,0] = 0
    for n in range(1, N):
        M = state_prob[:, n-1] * transition_matrix.T
        predecessor[:, n] = np.argmax(M, axis=1)
        state_prob[:, n] = M[range(K),predecessor[:, n]] * emission_matrix[:, n]
        # scale[n] = 1/sum(state_prob[:,n]);
        # normalize
        state_prob[:, n] = state_prob[:,n] / np.sum(state_prob[:,n])
    # Find Most probable state path
    path = np.zeros(N, dtype=int)
    # loop backwards from data points N-1 to end
    path[-1] = np.argmax(state_prob[:,-1])  # Last data point
    for n in range(N-2,-1,-1):
        path[n] = predecessor[path[n+1],n+1]
    # log_likelihood = -sum(log(scale));
    # Assign values to states (if state values are given).
    if state_vals is not None:
        path = path.astype(float)
        for (i, s) in enumerate(state_vals):
            path[path==i] = s
    return path