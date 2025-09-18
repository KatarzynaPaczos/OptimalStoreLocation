import numpy as np

W_CUSTOM = 1.0
W_STORE  = 1.5
W_RATIO = 0.1
MAX_RADIUS = 1000.0   # cutoff in meters


def customers_proximity(distances, n_residents):
    return W_CUSTOM * np.sum((1 - (distances/MAX_RADIUS)**(1/3)) * n_residents / 1000) # in K


def other_store_proximity(distances):
    return - W_STORE * np.sum((1 - (distances/MAX_RADIUS))**(1/3))


def ratio_customers_per_store(n_residents, dists_stores):
    return W_RATIO * np.sum(n_residents)/(len(dists_stores)) # in K


def evaluate_fn(x, tree_residents, tree_store, residents_xy, residents_n, stores_xy):
    cust_prox, store_prox, ratio = evaluate_score(x, tree_residents, tree_store, residents_xy, residents_n, stores_xy)
    return float(cust_prox + store_prox + ratio)


def evaluate_score(x, tree_residents, tree_store, residents_xy, residents_n, stores_xy):
    # x is the candidate for the new store. Let's calulate how good is this localisation
    idx = tree_residents.query_radius(x.reshape(1, -1), r=MAX_RADIUS)[0] # indexes of all residents in the max_radious around x
    dists_residents = np.linalg.norm(residents_xy[idx] - x, axis=1) # distances - vector with

    idx = tree_store.query_radius(x.reshape(1, -1), r=MAX_RADIUS)[0] # indexes of all residents in the max_radious around x
    dists_stores = np.linalg.norm(stores_xy[idx] - x, axis=1) # distances - vector with

    cust_prox = customers_proximity(dists_residents, residents_n[idx])
    store_prox = other_store_proximity(dists_stores)
    if len(dists_stores) == 0:
        ratio = len(residents_n[idx])*2
    else:
        ratio = ratio_customers_per_store(residents_n[idx], dists_stores)
    return cust_prox, store_prox, ratio
