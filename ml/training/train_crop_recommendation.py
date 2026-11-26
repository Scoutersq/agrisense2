import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "ml" / "datasets" / "raw" / "Crop_recommendation.csv"
MODEL_DIR = ROOT / "ml" / "saved_models"
METRICS_PATH = MODEL_DIR / "crop_recommendation_metrics.json"
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(DATA_PATH)
    frame = frame.drop_duplicates().dropna()

    missing = set(FEATURES + ["label"]) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    X = frame[FEATURES]
    y = frame["label"]
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.20, random_state=42, stratify=y_encoded
    )

    models = {
        "decision_tree": DecisionTreeClassifier(max_depth=12, random_state=42),
        "knn": Pipeline([
            ("scale", StandardScaler()),
            ("model", KNeighborsClassifier(n_neighbors=7)),
        ]),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1,
        ),
        "xgboost": XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=42,
        ),
    }

    results = {}
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    for name, model in models.items():
        cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="accuracy", n_jobs=-1)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        results[name] = {
            "cv_accuracy_mean": float(cv_scores.mean()),
            "cv_accuracy_std": float(cv_scores.std()),
            "test_accuracy": float(accuracy_score(y_test, predictions)),
        }

    best_name = max(results, key=lambda name: results[name]["test_accuracy"])
    best_model = models[best_name]

    joblib.dump(
        {
            "model": best_model,
            "features": FEATURES,
            "target": "label",
            "dataset_source": "Siddharth S. / Kaggle Crop Recommendation Dataset",
            "license": "Attribution 3.0 IGO (CC BY 3.0 IGO)",
            "label_encoder": label_encoder,
        },
        MODEL_DIR / "crop_recommendation.joblib",
    )

    predictions = best_model.predict(X_test)
    report = classification_report(
        y_test,
        predictions,
        labels=range(len(label_encoder.classes_)),
        target_names=label_encoder.classes_,
        output_dict=True,
        zero_division=0,
    )
    output = {
        "dataset": {
            "rows_after_cleaning": int(len(frame)),
            "features": FEATURES,
            "classes": sorted(y.unique().tolist()),
            "split": {"train": 0.80, "test": 0.20, "random_state": 42},
        },
        "models": results,
        "best_model": best_name,
        "test_classification_report": report,
    }
    METRICS_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
