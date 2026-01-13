from sklearn.multioutput import MultiOutputRegressor, RegressorChain
from interpret.glassbox import ExplainableBoostingRegressor



# MULTI OUTPUT REGRESSOR ----------------------------------------------------
model = MultiOutputRegressor(
    ExplainableBoostingRegressor(
        random_state=42,
        # EBM specific parameters you can tune:
        # max_bins=256,
        # max_interaction_bins=32,
        # interactions=10,  # number of pairwise interactions to consider
        # outer_bags=8,  # for bagging
        # inner_bags=0,
        # learning_rate=0.01,
        # validation_size=0.15,
        # early_stopping_rounds=50,
        # n_jobs=-1
    ))



# REGRESSOR CHAIN -----------------------------------------------------------
# model = RegressorChain(
#     ExplainableBoostingRegressor(
#         random_state=42
#     ),
#     order=order_regressorChain
# )