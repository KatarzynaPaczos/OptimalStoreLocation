from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, ConstantKernel
import numpy as np
from src.utils import Sobol
from src.score import evaluate_fn

class SimpleBayesOpt:
    def __init__(self, bounds, tree_res, tree_store, residents_xy, residents_n, stores_xy, k=1):
        self.bounds = np.array(bounds)
        self.residents_xy = residents_xy
        self.residents_n = residents_n
        self.stores_xy = stores_xy
        self.tree_res=tree_res
        self.tree_store=tree_store
        self.k = k
        self.X, self.y = [], []
        kernel = Matern(nu=2.5) * ConstantKernel(1.0, (1e-3, 1e3))
        self.gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True)
    
    def add_point(self, x):
        y = evaluate_fn(x, self.tree_res,
                        self.tree_store, self.residents_xy,
                        self.residents_n, self.stores_xy)
        self.X.append(x)
        self.y.append(y)

    def fit(self, X):
        for x in X:
            self.add_point(x)
        self.gp.fit(np.array(self.X), np.array(self.y))
        #print("GP fitted on", len(self.X), "points")

    def suggest_next(self, X_cand, n_best):
        """Predict UCB for candidates and return the best"""
        mu, sigma = self.gp.predict(X_cand, return_std=True) # type: ignore
        ucb = mu.ravel() + self.k * sigma
        top_idx = np.argsort(ucb)[-n_best:][::-1]  # indices of top n UCB values
        return X_cand[top_idx]
    
    def suggest(self, n_best, n_candidates=65536):
        # sample Sobol candidates
        Xcand = Sobol(n_candidates, bound_x=self.bounds[:,0], bound_y=self.bounds[:,1])
        #print(f"suggested 50 out of {int(2 ** np.ceil(np.log2(n_candidates)))} points")
        return self.suggest_next(Xcand, n_best)
    
    def run(self, first_data, n_iter=3):
        for i in range(n_iter):
            if i == 0:
                self.fit(first_data)
            else:
                best_loc = self.suggest(n_best = 50)
                self.fit(best_loc)
    
    def show_best(self, n=5):
        best_indices = np.argsort(self.y)[-n:][::-1]
        x, _ = np.array(self.X), np.array(self.y)
        return x[best_indices]
    