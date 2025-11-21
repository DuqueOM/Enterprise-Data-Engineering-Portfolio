#!/usr/bin/env python3
"""
Baseline model training script for PYME QA dataset.
Trains a simple text classification model to detect data quality issues.
"""
import json
import logging
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_synthetic_labels(df):
    """Create synthetic labels for baseline training based on text characteristics."""
    labels = []

    for _, row in df.iterrows():
        text = row["text"].lower()

        # Simple heuristic classification
        if any(
            keyword in text
            for keyword in ["procedimiento", "requisito", "tramite", "solicitud"]
        ):
            labels.append("procedimiento")
        elif any(keyword in text for keyword in ["costo", "precio", "tarifa", "valor"]):
            labels.append("costos")
        elif any(
            keyword in text for keyword in ["documento", "identidad", "cedula", "rut"]
        ):
            labels.append("documentacion")
        elif any(keyword in text for keyword in ["tiempo", "plazo", "dias", "meses"]):
            labels.append("tiempos")
        elif any(
            keyword in text
            for keyword in ["contacto", "telefono", "direccion", "email"]
        ):
            labels.append("contacto")
        else:
            labels.append("general")

    return labels


def extract_text_features(df):
    """Extract additional text features."""
    features = pd.DataFrame()

    # Text length features
    features["text_length"] = df["text"].str.len()
    features["word_count"] = df["text"].str.split().str.len()
    features["sentence_count"] = df["text"].str.count(r"[.!?]+")

    # Special character features
    features["has_numbers"] = df["text"].str.contains(r"\d").astype(int)
    features["has_emails"] = df["text"].str.contains(r"\S+@\S+").astype(int)
    features["has_urls"] = df["text"].str.contains(r"https?://\S+").astype(int)
    features["has_phone"] = (
        df["text"]
        .str.contains(r"(\+\d{1,3}[-.]?)?\d{3}[-.]?\d{3}[-.]?\d{4}")
        .astype(int)
    )

    # Question/answer indicators
    features["has_question"] = df["text"].str.contains(r"\?").astype(int)
    features["starts_with_question"] = (
        df["text"].str.startswith(r"¿|qué|cómo|dónde|cuándo|por qué").astype(int)
    )

    return features


def train_baseline_model(df):
    """Train a baseline classification model."""
    logger.info("Creating synthetic labels for baseline training...")
    labels = create_synthetic_labels(df)

    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)

    # Extract features
    logger.info("Extracting text features...")
    text_features = extract_text_features(df)

    # TF-IDF features
    vectorizer = TfidfVectorizer(
        max_features=1000, stop_words=None, ngram_range=(1, 2), min_df=2, max_df=0.95
    )
    tfidf_features = vectorizer.fit_transform(df["text"])

    # Combine features
    from scipy.sparse import hstack

    X = hstack([tfidf_features, text_features])

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train model
    logger.info("Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    logger.info(f"Model accuracy: {accuracy:.3f}")

    # Generate classification report
    class_names = label_encoder.classes_
    report = classification_report(
        y_test, y_pred, target_names=class_names, output_dict=True
    )

    # Feature importance
    feature_names = (
        vectorizer.get_feature_names_out().tolist() + text_features.columns.tolist()
    )
    importances = model.feature_importances_

    # Get top features
    top_indices = np.argsort(importances)[-10:][::-1]
    top_features = [(feature_names[i], importances[i]) for i in top_indices]

    return {
        "model": model,
        "vectorizer": vectorizer,
        "label_encoder": label_encoder,
        "feature_columns": text_features.columns.tolist(),
        "accuracy": accuracy,
        "classification_report": report,
        "top_features": top_features,
    }


def save_model_artifacts(model_data, output_dir):
    """Save model artifacts and metrics."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Save model
    model_path = output_dir / "baseline_model.pkl"
    joblib.dump(
        {
            "model": model_data["model"],
            "vectorizer": model_data["vectorizer"],
            "label_encoder": model_data["label_encoder"],
            "feature_columns": model_data["feature_columns"],
        },
        model_path,
    )

    logger.info(f"Model saved to {model_path}")

    # Save metrics
    metrics_path = output_dir / "metrics.json"
    metrics = {
        "accuracy": model_data["accuracy"],
        "classification_report": model_data["classification_report"],
        "top_features": model_data["top_features"],
        "model_type": "RandomForest",
        "feature_count": len(model_data["feature_columns"])
        + model_data["vectorizer"].max_features,
        "training_date": pd.Timestamp.now().isoformat(),
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    logger.info(f"Metrics saved to {metrics_path}")

    return metrics


def main():
    """Main function to train baseline model."""
    input_file = "data/processed/faqs_clean.jsonl"
    output_dir = "models"
    metrics_dir = "metrics"

    # Create directories
    Path(output_dir).mkdir(exist_ok=True)
    Path(metrics_dir).mkdir(exist_ok=True)

    # Load data
    logger.info(f"Loading data from {input_file}")
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return

    df = pd.read_json(input_file, lines=True)
    logger.info(f"Loaded {len(df)} records")

    if len(df) < 10:
        logger.warning("Very small dataset. Baseline model may not be meaningful.")

    # Train model
    model_data = train_baseline_model(df)

    # Save artifacts
    metrics = save_model_artifacts(model_data, output_dir)

    # Save metrics for DVC
    dvc_metrics_path = Path(metrics_dir) / "baseline_model.json"
    with open(dvc_metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    logger.info("🎉 Baseline model training completed!")
    logger.info(f"Model accuracy: {metrics['accuracy']:.3f}")

    # Print summary
    logger.info("\n📊 Model Summary:")
    logger.info(f"   - Accuracy: {metrics['accuracy']:.3f}")
    logger.info(f"   - Feature count: {metrics['feature_count']}")
    logger.info(
        f"   - Top features: {[feat[0] for feat in metrics['top_features'][:5]]}"
    )


if __name__ == "__main__":
    main()
