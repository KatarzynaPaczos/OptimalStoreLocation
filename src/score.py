import numpy as np

W_CUSTOM = 1.0
W_STORE  = 1.0
W_RATIO = 1.0
MAX_RADIUS = 1000.0   # cutoff in meters
EXPECTED_CUST_PER_STORE = 800


def customers_proximity(distances, n_residents):
    ''' In 1km distance - how close is the store to the people'''
    n_residents = n_residents.reshape(-1)
    weights = 1 - (distances / MAX_RADIUS) ** (1/3)
    return W_CUSTOM * np.sum(weights *n_residents) / np.sum(n_residents)

def other_store_proximity(distances):
    ''' In 1km distance - howclose are the existing stores'''
    return - W_STORE * np.sum((1 - (distances/MAX_RADIUS))**(1/3))/ len(distances)


def ratio_customers_per_store(n_residents, dists_stores):
    customers_per_store = np.sum(n_residents) / len(dists_stores) if len(dists_stores) > 0 else np.sum(n_residents)*2
    return W_RATIO * np.min([customers_per_store/ EXPECTED_CUST_PER_STORE, 1])


def evaluate_fn(x, tree_residents, tree_store, residents_xy, residents_n, stores_xy):
    cust_prox, store_prox, ratio = evaluate_score(x, tree_residents, tree_store, residents_xy, residents_n, stores_xy)
    return float(1 + cust_prox + store_prox + ratio)


def evaluate_score(x, tree_residents, tree_store, residents_xy, residents_n, stores_xy):
    # x is the candidate for the new store. Let's calulate how good is this localisation
    # indexes of all residents in the max_radious around x
    idx_res = tree_residents.query_radius(x.reshape(1, -1), r=MAX_RADIUS)[0]
    dists_residents = np.linalg.norm(residents_xy[idx_res] - x, axis=1) # distances - vector with

    idx_store = tree_store.query_radius(x.reshape(1, -1), r=MAX_RADIUS)[0]
    dists_stores = np.linalg.norm(stores_xy[idx_store] - x, axis=1) # distances - vector with

    cust_prox = customers_proximity(dists_residents, residents_n[idx_res]) if len(dists_residents) > 0 else 0.0
    store_prox = other_store_proximity(dists_stores) if len(dists_stores) > 0 else 0.0
    ratio = ratio_customers_per_store(residents_n[idx_res], dists_stores)
    return cust_prox, store_prox, ratio
