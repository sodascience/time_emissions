from __future__ import annotations
from dataclasses import dataclass
import polars as pl
import numpy as np

from sklearn.base import BaseEstimator, RegressorMixin



@dataclass(eq = False)
class GroupedMeanRegressor(RegressorMixin, BaseEstimator):
    group_col: str | None = None
    recode: dict | None = None

    def _groups(self, X) -> pl.Series:
        X = pl.DataFrame(X)
        if self.group_col not in X.columns:
            raise ValueError(f"Group column '{self.group_col} is not in X")
        g = X[self.group_col]
        if self.recode is None:
            return g
        return g.cast(pl.String).replace_strict(self.recode)

    
    def fit(self, X, Y) -> "GroupedMeanRegressor":

        g = self._groups(X)
        Y = pl.DataFrame(np.asarray(Y).reshape(len(g), -1))

        if self.group_col not in X.columns:
            raise ValueError(f"Group column '{self.group_col}' is not in X")
        
        self.global_means_ = Y.mean().row(0, named = True)
        self.group_means_ = Y.with_columns(g).group_by(self.group_col).mean()
        return self


    def predict(self, X: pl.DataFrame) -> np.ndarray:        
        pred = (self._groups(X).to_frame()
                .with_row_index("row")
                .join(self.group_means_, on = self.group_col, how = "left")
                .sort("row")
                .select(pl.col(c).fill_null(m) for c, m in self.global_means_.items())
                .to_numpy())
        
        return pred.ravel() if pred.shape[1] == 1 else pred