#!/usr/bin/env python3
"""
Metrics collection script for DVC pipeline.
Generates JSON metrics files for each stage.
"""
import json
import os
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def collect_ingest_metrics():
    """Collect metrics after data ingestion."""
    metrics = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "stage": "ingest",
        "status": "completed"
    }
    
    # Check if output file exists
    output_file = "data/processed/faqs.jsonl"
    if os.path.exists(output_file):
        df = pd.read_json(output_file, lines=True)
        metrics["records_processed"] = len(df)
        metrics["unique_sources"] = df['source_url'].nunique()
        metrics["regions"] = df['region'].nunique()
        logger.info(f"Ingested {len(df)} records from {metrics['unique_sources']} sources")
    else:
        metrics["error"] = "Output file not found"
    
    return metrics

def collect_clean_metrics():
    """Collect metrics after data cleaning."""
    metrics = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "stage": "clean",
        "status": "completed"
    }
    
    # Compare input vs output
    input_file = "data/processed/faqs.jsonl"
    output_file = "data/processed/faqs_clean.jsonl"
    
    if os.path.exists(input_file) and os.path.exists(output_file):
        input_df = pd.read_json(input_file, lines=True)
        output_df = pd.read_json(output_file, lines=True)
        
        metrics["input_records"] = len(input_df)
        metrics["output_records"] = len(output_df)
        metrics["duplicates_removed"] = len(input_df) - len(output_df)
        metrics["deduplication_rate"] = metrics["duplicates_removed"] / len(input_df) * 100
        
        logger.info(f"Cleaned: {metrics['duplicates_removed']} duplicates removed")
    else:
        metrics["error"] = "Input or output file not found"
    
    return metrics

def collect_validation_metrics():
    """Collect metrics after validation."""
    metrics = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "stage": "validation",
        "status": "completed"
    }
    
    # Check validation results
    output_file = "data/processed/faqs_clean.jsonl"
    if os.path.exists(output_file):
        df = pd.read_json(output_file, lines=True)
        metrics["validated_records"] = len(df)
        metrics["validation_passed"] = True
        
        # Basic validation checks
        missing_values = df.isnull().sum().sum()
        metrics["missing_values"] = int(missing_values)
        metrics["completeness_rate"] = (1 - missing_values / (len(df) * len(df.columns))) * 100
        
        logger.info(f"Validation completed for {len(df)} records")
    else:
        metrics["error"] = "Output file not found"
        metrics["validation_passed"] = False
    
    return metrics

def save_metrics(metrics, filename):
    """Save metrics to JSON file."""
    metrics_dir = Path("metrics")
    metrics_dir.mkdir(exist_ok=True)
    
    output_path = metrics_dir / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Metrics saved to {output_path}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        logger.error("Usage: python metrics.py <stage>")
        sys.exit(1)
    
    stage = sys.argv[1]
    
    if stage == "ingest":
        metrics = collect_ingest_metrics()
        save_metrics(metrics, "ingest.json")
    elif stage == "clean":
        metrics = collect_clean_metrics()
        save_metrics(metrics, "clean.json")
    elif stage == "validation":
        metrics = collect_validation_metrics()
        save_metrics(metrics, "validation.json")
    else:
        logger.error(f"Unknown stage: {stage}")
        sys.exit(1)
