import numpy as np
from sklearn.neighbors import KDTree

# tests/test_score.py
import os
import sys

print("PYTEST DEBUG cwd:", os.getcwd())
print("PYTEST DEBUG sys.path:", sys.path)

from src.score import (
    customers_proximity,
    other_store_proximity,
    evaluate_score,
)

def test_customers_proximity_more_customers_higher_score():
    # same distances, different number of residents
    d = np.array([100.0, 200.0])
    few = np.array([10.0, 10.0])
    many = np.array([50.0, 50.0])

    score_few = customers_proximity(d, few)
    score_many = customers_proximity(d, many)

    # more people at same distance -> better score
    assert score_many > score_few


def test_customers_proximity_closer_is_better():
    # same residents, closer distances should give higher score
    close = np.array([50.0, 100.0])
    far = np.array([500.0, 800.0])
    n_residents = np.array([30.0, 30.0])

    score_close = customers_proximity(close, n_residents)
    score_far = customers_proximity(far, n_residents)

    assert score_close > score_far