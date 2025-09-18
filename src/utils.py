from scipy.stats import qmc
import numpy as np

def Sobol(candidates, bound_x, bound_y):
    sampler = qmc.Sobol(d=2, scramble=True)
    sample = sampler.random(int(2 ** np.ceil(np.log2(candidates))))
    scaled = qmc.scale(sample, bound_x, bound_y)
    return scaled
