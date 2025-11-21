import numpy as np
from sklearn.neighbors import KDTree

from src.score import (
    customers_proximity,
    other_store_proximity,
    ratio_customers_per_store,
    evaluate_score,
    evaluate_fn,
    MAX_RADIUS,
)


def test_customers_proximity_range_and_monotonic():
    distances = np.array([100.0, 500.0, 900.0])
    residents = np.array([10.0, 20.0, 30.0])

    val = customers_proximity(distances, residents)
    assert 0.0 <= val <= 1.0

    # closer = better
    close = customers_proximity(np.array([100.0]), np.array([100.0]))
    far = customers_proximity(np.array([900.0]), np.array([100.0]))
    assert close > far


def test_other_store_proximity_range_and_penalty():
    # two stores close
    distances_close = np.array([100.0, 200.0])
    # two stores far
    distances_far = np.array([800.0, 900.0])

    val_close = -other_store_proximity(distances_close)
    val_far = -other_store_proximity(distances_far)

    # range 0-1
    assert 0.0 <= val_close <= 1.0
    assert 0.0 <= val_far <= 1.0
    assert val_far < val_close


def test_ratio_customers_per_store_range_and_behavior():
    n_residents = np.array([400.0, 400.0])
    dists_stores = np.array([100.0])
    val = ratio_customers_per_store(n_residents, dists_stores)
    assert 0.0 <= val <= 1.0

    # more customers -> bigger ratio
    few_customers = np.array([200.0])
    many_customers = np.array([1600.0])

    val_few = ratio_customers_per_store(few_customers, dists_stores)
    val_many = ratio_customers_per_store(many_customers, dists_stores)

    assert val_many > val_few
    assert val_many <= 1.0
    val_no_stores = ratio_customers_per_store(n_residents, np.array([]))
    assert val_no_stores == 1.0


def test_evaluate_score_components_and_total_range():
    # simple: 2 buildings, 1 store far away, 1 store close
    residents_xy = np.array([[0.0, 0.0], [500.0, 0.0]])
    residents_n = np.array([100.0, 100.0])
    stores_xy = np.array([[2000.0, 0.0]])
    tree_residents = KDTree(residents_xy)
    tree_stores = KDTree(stores_xy)

    x = np.array([100.0, 0.0])  # candidate location

    cust_prox, store_prox, ratio = evaluate_score(
        x, tree_residents, tree_stores, residents_xy, residents_n, stores_xy
    )

    assert 0.0 <= cust_prox <= 1.0
    assert 0.0 <= store_prox <= 1.0
    assert 0.0 <= ratio <= 1.0

    total = 1 + cust_prox + store_prox + ratio
    assert 0.0 <= total <= 3.0

    # evaluate_fn should give the same total
    fn_val = evaluate_fn(x, tree_residents, tree_stores, residents_xy, residents_n, stores_xy)
    assert np.isclose(fn_val, total)
