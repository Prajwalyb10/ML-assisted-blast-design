from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


OUTPUT_COLUMNS = [
    "Burden (m)",
    "Spacing (m)",
    "Charge per Hole (kg)",
    "Stemming Length (m)",
    "Sub Drilling (m)",
    "Flyrock Distance (m)",
]

TARGET_ALIASES = {
    "Burden (m)": "burden",
    "Spacing (m)": "spacing",
    "Charge per Hole (kg)": "charge_per_hole",
    "Stemming Length (m)": "stemming_length",
    "Sub Drilling (m)": "sub_drilling",
    "Flyrock Distance (m)": "flyrock_distance",
}

TARGET_LABELS = {
    "burden": "Burden (m)",
    "spacing": "Spacing (m)",
    "charge_per_hole": "Charge per Hole (kg)",
    "stemming_length": "Stemming Length (m)",
    "sub_drilling": "Sub Drilling (m)",
    "flyrock_distance": "Flyrock Distance (m)",
}

ROCK_TYPE_OPTIONS = {
    1: "Limestone",
    3: "Shale",
    4: "Sandstone",
    5: "Basalt",
    6: "Granite",
}

EXPLOSIVE_TYPE_OPTIONS = {
    1: "Emulsion",
    2: "ANFO",
    3: "Slurry",
}

INITIATION_SEQUENCE_OPTIONS = {
    1: "Line",
    2: "Staggered",
    3: "Diagonal",
    4: "V-Pattern",
}

MODEL_TEMPLATES = {
    "burden": Pipeline([
        ("scaler", StandardScaler()),
        ("model", Ridge(alpha=1.0)),
    ]),
    "spacing": Pipeline([
        ("scaler", StandardScaler()),
        ("model", ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42)),
    ]),
    "charge_per_hole": RandomForestRegressor(
        n_estimators=350,
        max_depth=12,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=1,
    ),
    "stemming_length": RandomForestRegressor(
        n_estimators=500,
        max_depth=10,
        random_state=42,
        n_jobs=1,
    ),
    "sub_drilling": Pipeline([
        ("scaler", StandardScaler()),
        ("model", Ridge(alpha=0.5)),
    ]),
    "flyrock_distance": RandomForestRegressor(
        n_estimators=450,
        max_depth=14,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=1,
    ),
}


@dataclass
class TrainedTarget:
    alias: str
    column: str
    features: list[str]
    model: Any
    r2: float
    rmse: float
    minimum: float
    maximum: float


def rock_code_to_category(rock_code: int) -> str:
    if rock_code >= 5:
        return "hard"
    if rock_code <= 3:
        return "soft"
    return "medium"


class BlastMLService:
    def __init__(self, dataset_path: str | Path):
        self.dataset_path = Path(dataset_path)
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        self.df = pd.read_csv(self.dataset_path)
        self.input_columns = [c for c in self.df.columns if c not in OUTPUT_COLUMNS]
        self.targets: Dict[str, TrainedTarget] = {}
        self.reference_data: Dict[str, Any] = {}
        self.selected_features = self._select_features()
        self._train_models()
        self._build_reference_data()

    def _select_features(self) -> list[str]:
        X = self.df[self.input_columns]
        Y = self.df[OUTPUT_COLUMNS]
        selector = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=1)
        selector.fit(X, Y)

        importance_df = (
            pd.DataFrame({"feature": self.input_columns, "importance": selector.feature_importances_})
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )
        chosen = importance_df[importance_df["importance"] > 0.015]["feature"].tolist()
        return chosen or importance_df.head(12)["feature"].tolist()

    def _train_models(self) -> None:
        X = self.df[self.selected_features]

        for column in OUTPUT_COLUMNS:
            alias = TARGET_ALIASES[column]
            y = self.df[column]
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            model = clone(MODEL_TEMPLATES[alias])
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            self.targets[alias] = TrainedTarget(
                alias=alias,
                column=column,
                features=list(self.selected_features),
                model=model,
                r2=float(r2_score(y_test, y_pred)),
                rmse=float(root_mean_squared_error(y_test, y_pred)),
                minimum=float(y.min()),
                maximum=float(y.max()),
            )

    def _build_reference_data(self) -> None:
        defaults = {}
        ranges = {}
        for column in self.selected_features:
            series = self.df[column]
            defaults[column] = float(series.median()) if pd.api.types.is_numeric_dtype(series) else series.mode().iloc[0]
            ranges[column] = {
                "min": float(series.min()),
                "max": float(series.max()),
                "median": defaults[column],
            }

        self.reference_data = {
            "dataset_path": str(self.dataset_path),
            "selected_features": self.selected_features,
            "defaults": defaults,
            "ranges": ranges,
            "options": {
                "rock_type": ROCK_TYPE_OPTIONS,
                "explosive_type": EXPLOSIVE_TYPE_OPTIONS,
                "initiation_sequence": INITIATION_SEQUENCE_OPTIONS,
            },
            "model_metrics": {
                alias: {
                    "target": trained.column,
                    "r2": round(trained.r2, 4),
                    "rmse": round(trained.rmse, 4),
                }
                for alias, trained in self.targets.items()
            },
        }

    def predict(self, raw_features: Dict[str, Any]) -> Dict[str, float]:
        features = pd.DataFrame([{name: raw_features[name] for name in self.selected_features}])
        predictions: Dict[str, float] = {}

        for alias, trained in self.targets.items():
            value = float(trained.model.predict(features)[0])
            bounded = min(max(value, trained.minimum), trained.maximum)
            predictions[alias] = round(bounded, 3)

        return predictions

    def build_feature_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        feature_values = {column: payload[column] for column in self.input_columns if column in payload}
        feature_values["Hole Depth (m)"] = max(
            float(feature_values["Hole Depth (m)"]),
            float(feature_values["Bench Height (m)"]),
        )
        return feature_values

    def summarize_inputs(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        rock_code = int(payload["Rock Type (Limestone-1,Shale-3,Sandstone-4,Basalt-5,Granite-6)"])
        explosive_code = int(payload["Explosive Type(Emulsion-1,ANFO-2,Slurry-3)"])
        initiation_code = int(payload["Initiation Sequence (Line-1,Staggered-2,Diagonal-3,Vpattern-4)"])
        return {
            "rock_type_code": rock_code,
            "rock_type_label": ROCK_TYPE_OPTIONS.get(rock_code, str(rock_code)),
            "rock_category": rock_code_to_category(rock_code),
            "explosive_type_code": explosive_code,
            "explosive_type_label": EXPLOSIVE_TYPE_OPTIONS.get(explosive_code, str(explosive_code)),
            "initiation_sequence_code": initiation_code,
            "initiation_sequence_label": INITIATION_SEQUENCE_OPTIONS.get(initiation_code, str(initiation_code)),
        }
