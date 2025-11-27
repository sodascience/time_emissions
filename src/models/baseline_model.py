import pandas as pd
import polars as pl
from sklearn.base import BaseEstimator, RegressorMixin



class GroupMeanRegressor(BaseEstimator, RegressorMixin):
    def __init__(self, group_feature: str):
        self.group_feature = group_feature                      # define group feature

    def fit(self, x: pl.DataFrame, y: pl.DataFrame):
        self.means_ = y.group_by(x[self.group_feature]).mean()   # get mean per group_feature
        return self
    
    def predict(self, x: pl.DataFrame):
            pred = (x
                    .join(self.means_, on = self.group_feature, how = "left")               # "predict" the means per group_feature by joining
                    .select([c for c in self.means_.columns if c != self.group_feature])    # only keep the predicted columns
            )

            return pred
    
    


class MeanRegressor(BaseEstimator, RegressorMixin):
    def fit(self, x: pl.DataFrame, y: pd.DataFrame):
        self.mean_ = [float(v) for v in y.mean().row(0)]
        self.columns_ = y.columns
        return self
    
    def predict(self, x: pl.DataFrame):
            n = x.height
            pred = pl.DataFrame(
                 data = {col: [mean] * n for col, mean in zip(self.columns_, self.mean_)})

            return pred