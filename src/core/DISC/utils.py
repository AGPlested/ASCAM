import numpy as np

def normal_pdf(x, mu=0, sigma=1):
    return np.exp(-0.5 * ((x-mu)/sigma)**2) / (np.sqrt(2*np.pi) * sigma)

def next_state(ci, TM):
    """
    Sample the next state in the Markov chain specified by the transition
    matrix given the current state.
    Input:
        ci - index of the current state
        TM - numpy array containing the transition matrix
    Output:
        index of the next state
    """
    return np.random.choice(range(TM.shape[1]),
                            p=TM[ci, :])

def sample_chain(TM, si, n=10):
    """
    Generate a sample from the Markov chain specified by the transition
    matrix in `TM` beginning in state with index `si`.
    Input:
        TM - numpy array containing the transition matrix
        si - index of the initial state
        n - integer length of the sample
    Output:
        numpy array containing the indices of the states
    """
    sample =  np.zeros(n, dtype=int)
    sample[0] = si
    for i in range(1,n):
        sample[i] = next_state(sample[i-1], TM)
    return sample
