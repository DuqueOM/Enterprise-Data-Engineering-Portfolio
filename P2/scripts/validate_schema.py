#!/usr/bin/env python3
"""
Data validation script for PYME QA dataset.
Validates schema compliance and basic data quality metrics.
"""
import json
import sys
import os
import pandas as pd
from jsonschema import validate, ValidationError
import pandera as pa
from pandera import DataFrameModel, Column, Check
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# JSON Schema for validation
SCHEMA = {
    "type": "object",
    "required": ["id", "source_url", "text", "date_fetched"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "source_url": {"type": "string", "format": "uri"},
        "text": {"type": "string", "minLength": 10},
        "date_fetched": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
        "region": {"type": "string"}
    },
    "additionalProperties": True
}

# Pandera schema for advanced validation
class QADatasetSchema(DataFrameModel):
    id: Column(str, Check.str_length(min=1))
    source_url: Column(str, Check.str_matches(r"https?://.*"))
    text: Column(str, Check.str_length(min=10))
    date_fetched: Column(str, Check.str_matches(r"\d{4}-\d{2}-\d{2}"))
    region: Column(str, nullable=True)

def validate_jsonl_file(file_path):
    """Validate JSONL file against schema and compute quality metrics."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    records = []
    errors = []
    line_count = 0
    
    logger.info(f"Validating {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line_count += 1
                try:
                    record = json.loads(line.strip())
                    validate(instance=record, schema=SCHEMA)
                    records.append(record)
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: Invalid JSON - {e}")
                except ValidationError as e:
                    errors.append(f"Line {line_num}: Schema validation failed - {e.message}")
    
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        return False
    
    # Convert to DataFrame for advanced validation
    if records:
        df = pd.DataFrame(records)
        
        # Pandera validation
        try:
            QADatasetSchema.validate(df)
            logger.info("✅ Pandera schema validation passed")
        except pa.errors.SchemaErrors as e:
            errors.extend([f"Pandera validation: {err}" for err in e.failure_cases])
        
        # Quality metrics
        logger.info(f"📊 Quality Metrics for {file_path}:")
        logger.info(f"   - Total records: {len(records)}")
        logger.info(f"   - Valid records: {len(records) - len(errors)}")
        logger.info(f"   - Invalid records: {len(errors)}")
        logger.info(f"   - Average text length: {df['text'].str.len().mean():.1f} chars")
        logger.info(f"   - Unique sources: {df['source_url'].nunique()}")
        logger.info(f"   - Regions: {df['region'].value_counts().to_dict()}")
        
        # Check for duplicates
        duplicates = df.duplicated(subset=['text']).sum()
        if duplicates > 0:
            logger.warning(f"⚠️  Found {duplicates} duplicate text entries")
        
        # Check for empty or very short texts
        short_texts = (df['text'].str.len() < 50).sum()
        if short_texts > 0:
            logger.warning(f"⚠️  Found {short_texts} very short text entries (< 50 chars)")
    
    # Report errors
    if errors:
        logger.error("❌ Validation errors found:")
        for error in errors[:10]:  # Show first 10 errors
            logger.error(f"   {error}")
        if len(errors) > 10:
            logger.error(f"   ... and {len(errors) - 10} more errors")
        return False
    else:
        logger.info("✅ All validations passed!")
        return True

def main():
    """Main validation function."""
    data_file = "data/processed/faqs_clean.jsonl"
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    
    success = validate_jsonl_file(data_file)
    
    if success:
        logger.info("🎉 Data validation completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Data validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
