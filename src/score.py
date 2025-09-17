import numpy as np
from sklearn.neighbors import KDTree


R_COVER = 2000.0             # radious of "good access" (m)
MIN_GAP = 180.0             # minimal gap between new stores (m)
PENALTY_RADIUS = 1000.0    # radius to existing store to apply penalty (m)
# weights for score components - how important is
W_DEMAND_NEAR = 1.0         # resident proximity
W_COVER_GAIN  = 1.0         # new_covered residents
W_LOAD_IMPROV = 1.0         # load store imporvement
W_PENALTY     = 1.0         # there is a store closeby - penalty
MAX_RADIUS = 500.0   # cutoff in meters

def evaluate_fn(x, residents_xy, residents_n):
    # this function is really expensive computationally - we will make it better. 
    tree = KDTree(residents_xy)
    idx = tree.query_radius(x.reshape(1, -1), r=MAX_RADIUS)[0] # indexes of all residents in the max_radious around x
    if len(idx) == 0:
        return 0.0
    dists = np.linalg.norm(residents_xy[idx] - x, axis=1) # distances - vector with
    result = np.sum((1 - dists/MAX_RADIUS) * residents_n[idx]) # the sum is not only from the aparaments itself - also how many people lives there
    return float(result)