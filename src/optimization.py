import pandas as pd
import numpy as np
from src.utils import Sobol
from src.SimpleBayesOpt import SimpleBayesOpt
from data.utils import _latlon_to_xy, _xy_to_latlon
from src.score import evaluate_score, evaluate_fn
from sklearn.neighbors import KDTree

MARGIN = 1000.0

def make_sobol_candidates(residents_xy, n_candidates = 600, margin_m=MARGIN):
    xmin, ymin = residents_xy.min(axis=0) - margin_m
    xmax, ymax = residents_xy.max(axis=0) + margin_m
    return Sobol(candidates = n_candidates, bound_x = [xmin, ymin], bound_y =[xmax, ymax])


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
    new_locations_all = np.empty((0,2))
    scores_detailed = []

    for iteration_global in range(n):
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
        model.run(n_iter = 2, first_data = candidates_xy)
        new_locations_xy = model.show_best(1)
        new_locations_xy = random_search_local(new_locations_xy, 1000, tree_residents, tree_store,
                                                        residents_xy, residents_n, stores_xy)
        new_locations_all = np.vstack([new_locations_all, new_locations_xy])
        stores_xy = np.vstack([stores_xy, new_locations_xy])

        # when the locations are ready - calculate once again for visualisation
        for iter in new_locations_xy:
            cust_prox, store_prox, ratio = evaluate_score(iter, tree_residents, tree_store,
                                                        residents_xy, residents_n, stores_xy)
            score = cust_prox + store_prox + ratio
            scores_detailed.append([cust_prox, store_prox, ratio, score, iteration_global+1])

    new_locations_latlon = _xy_to_latlon(new_locations_all, ref_lat)
    return np.column_stack([new_locations_latlon, scores_detailed])


def random_search_local(new_locations_xy, distance, tree_residents, tree_store, residents_xy, residents_n, stores_xy):
    best_search = []
    for _, [lat_xy, lon_xy] in enumerate(new_locations_xy):
        bound_x = [lat_xy - distance, lon_xy - distance]
        bound_y = [lat_xy + distance, lon_xy + distance]
        sobol_points = Sobol(600, bound_x, bound_y)
        scores = [evaluate_fn(p, tree_residents, tree_store, residents_xy, residents_n, stores_xy) for p in sobol_points]
        best_local_point = sobol_points[np.argmax(scores)]
        best_search.append(best_local_point)
    return best_search
