import pandas as pd
import numpy as np
from scipy.stats import qmc
from src.SimpleBayesOpt import SimpleBayesOpt
from src.utils import _latlon_to_xy, _xy_to_latlon

MARGIN = 1000.0

def make_sobol_candidates(residents_xy, n_candidates=300, margin_m=MARGIN):
    xmin, ymin = residents_xy.min(axis=0) - margin_m
    xmax, ymax = residents_xy.max(axis=0) + margin_m

    sampler = qmc.Sobol(d=2, scramble=True)
    sample = sampler.random(int(2 ** np.ceil(np.log2(n_candidates))))
    scaled = qmc.scale(sample, [xmin, ymin], [xmax, ymax])
    return scaled


def find_best_location(housing: pd.DataFrame, store_locations: pd.DataFrame, n=5,
                       use_grid=True):
    """
    Returns DataFrame with the best n picks
    """
    ref_lat = float(np.mean(housing['centroid_lat'].to_numpy()))
    residents_xy = _latlon_to_xy(housing[['centroid_lat',  'centroid_lon']].to_numpy(), ref_lat)
    residents_n = housing[['residents']].to_numpy()
    store_locations = store_locations[['lat', 'lon']]
    stores_xy = _latlon_to_xy(store_locations.to_numpy(), ref_lat) # for later
    if use_grid:
        candidates_xy = make_sobol_candidates(residents_xy, margin_m=MARGIN)
    else:
        candidates_xy = residents_xy
    #show_candidates(candidates_xy, ref_lat)

    model = SimpleBayesOpt(bounds=[
                                (residents_xy[:,0].min(), residents_xy[:,0].max()),
                                (residents_xy[:,1].min(), residents_xy[:,1].max())
                            ],
                            residents_xy=residents_xy,
                            residents_n=residents_n)
    model.run(n_iter = 3, first_data = candidates_xy)
    new_locations_xy, score = model.show_best(n)
    new_locations_latlon = _xy_to_latlon(new_locations_xy, ref_lat)
    idx_col = np.arange(1, len(score)+1).reshape(-1, 1)
    return np.column_stack([new_locations_latlon, score, idx_col])
