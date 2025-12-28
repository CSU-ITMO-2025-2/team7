from typing import Any

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression

MODEL_SPECS: dict[str, dict[str, Any]] = {
    "LinearRegression": {
        "class": LinearRegression,
        "parameters": {
            "fit_intercept": {
                "type": "bool",
                "default": True,
                "options": [True, False],
            },
            "tol": {
                "type": "float",
                "default": 1e-6,
                "min": 0.0,
                "step": 1e-6,
            },
            "positive": {
                "type": "bool",
                "default": False,
                "options": [True, False],
            },
        },
    },
    "RandomForestRegressor": {
        "class": RandomForestRegressor,
        "parameters": {
            "n_estimators": {
                "type": "int",
                "default": 100,
                "min": 1,
                "step": 1,
            },
            "criterion": {
                "type": "enum",
                "default": "squared_error",
                "options": [
                    "squared_error",
                    "absolute_error",
                    "friedman_mse",
                    "poisson",
                ],
            },
            "max_depth": {
                "type": "int",
                "default": None,
                "min": 1,
                "step": 1,
                "nullable": True,
            },
        },
    },
    "GradientBoostingRegressor": {
        "class": GradientBoostingRegressor,
        "parameters": {
            "loss": {
                "type": "enum",
                "default": "squared_error",
                "options": ["squared_error", "absolute_error", "huber", "quantile"],
            },
            "learning_rate": {
                "type": "float",
                "default": 0.1,
                "min": 0.0,
                "step": 0.01,
            },
            "n_estimators": {
                "type": "int",
                "default": 100,
                "min": 1,
                "step": 1,
            },
            "subsample": {
                "type": "float",
                "default": 1.0,
                "min": 0.01,
                "max": 1.0,
                "step": 0.01,
            },
        },
    },
}


def get_model_catalog() -> dict[str, Any]:
    models: list[dict[str, Any]] = []
    for name, spec in MODEL_SPECS.items():
        params = []
        for param_name, param_spec in spec["parameters"].items():
            params.append({"name": param_name, **param_spec})
        models.append({"name": name, "parameters": params})
    return {"models": models}
