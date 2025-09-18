import pandas as pd
import numpy as np
from scipy.stats import qmc
from src.SimpleBayesOpt import SimpleBayesOpt
from data.utils import _latlon_to_xy, _xy_to_latlon
from src.score import evaluate_score
from sklearn.neighbors import KDTree

MARGIN = 1000.0

def make_sobol_candidates(residents_xy, n_candidates=300, margin_m=MARGIN):
    xmin, ymin = residents_xy.min(axis=0) - margin_m
    xmax, ymax = residents_xy.max(axis=0) + margin_m

    sampler = qmc.Sobol(d=2, scramble=True)
    sample = sampler.random(int(2 ** np.ceil(np.log2(n_candidates))))
    scaled = qmc.scale(sample, [xmin, ymin], [xmax, ymax])
    return scaled
#expect defould number of zabka stores -> one per 100m2


def find_best_location(housing: pd.DataFrame, store_locations: pd.DataFrame, n=5,
                       use_grid=True):
    """
    Returns DataFrame with the best n picks
    """
    ref_lat = float(np.mean(housing['lat'].to_numpy()))
    residents_xy = _latlon_to_xy(housing[['lat',  'lon']].to_numpy(), ref_lat)
    residents_n = housing[['residents']].to_numpy()
    store_locations = store_locations[['lat', 'lon']]
    stores_xy = _latlon_to_xy(store_locations.to_numpy(), ref_lat) # for later
    if use_grid:
        candidates_xy = make_sobol_candidates(residents_xy, margin_m=MARGIN)
    else:
        candidates_xy = residents_xy
    #show_candidates(candidates_xy, ref_lat)

    tree_residents = KDTree(residents_xy)
    tree_store = KDTree(stores_xy)

    model = SimpleBayesOpt(bounds=[
                                (residents_xy[:,0].min(), residents_xy[:,0].max()),
                                (residents_xy[:,1].min(), residents_xy[:,1].max())
                            ],
                            residents_xy=residents_xy,
                            residents_n=residents_n,
                            stores_xy=stores_xy,
                            tree_res=tree_residents,
                            tree_store=tree_store)
    model.run(n_iter = 3, first_data = candidates_xy)
    new_locations_xy= model.show_best(n)
    scores_detailed = []
    for iter in new_locations_xy:
        cust_prox, store_prox, ratio = evaluate_score(iter, tree_residents, tree_store,
                                                      residents_xy, residents_n, stores_xy)
        score = cust_prox + store_prox + ratio
        scores_detailed.append([cust_prox, store_prox, ratio, score])
    new_locations_latlon = _xy_to_latlon(new_locations_xy, ref_lat)
    idx_col = np.arange(1, len(new_locations_latlon)+1).reshape(-1, 1)
    return np.column_stack([new_locations_latlon, scores_detailed, idx_col])
