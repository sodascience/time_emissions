from sklearn.multioutput import MultiOutputRegressor, RegressorChain
from sklearn.ensemble import HistGradientBoostingRegressor



# MULTI OUTPUT REGRESSOR ----------------------------------------------------
model = MultiOutputRegressor(
    HistGradientBoostingRegressor(
        random_state = 42,
        categorical_features = "from_dtype" # from scikit-learn 1.2
        ))



# REGRESSOR CHAIN -----------------------------------------------------------
# model = RegressorChain(
#     HistGradientBoostingRegressor(
#         random_state = 42 # ,
#         # categorical_features = "from_dtype" # from scikit-learn 1.2
#     ),
#     order = order_regressorChain
# )