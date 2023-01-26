import numpy as np

def normal_pdf(x, mu=0, sigma=1):
    return np.exp(-0.5 * ((x-mu)/sigma)**2) / (np.sqrt(2*np.pi) * sigma)

