import json
import pytest
import pandas as pd
from jsonschema import validate, ValidationError
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Schema for validation
SCHEMA = {
    "type": "object",
    "required": ["id", "source_url", "text", "date_fetched"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "source_url": {"type": "string", "pattern": r"https?://.*"},
        "text": {"type": "string", "minLength": 10},
        "date_fetched": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
        "region": {"type": "string"}
    },
    "additionalProperties": True
}

def test_data_file_exists():
    """Test that the processed data file exists."""
    assert os.path.exists('data/processed/faqs_clean.jsonl'), "Processed data file not found"

def test_file_is_valid_jsonl():
    """Test that the file contains valid JSON lines."""
    with open('data/processed/faqs_clean.jsonl', 'r', encoding='utf8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                json.loads(line.strip())
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON on line {line_num}: {e}")

def test_lines_have_required_fields():
    """Test that all lines have required fields according to schema."""
    errors = []
    
    with open('data/processed/faqs_clean.jsonl', 'r', encoding='utf8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                obj = json.loads(line.strip())
                validate(instance=obj, schema=SCHEMA)
            except ValidationError as e:
                errors.append(f"Line {line_num}: {e.message}")
    
    if errors:
        pytest.fail(f"Schema validation errors: {errors[:5]}")  # Show first 5 errors

def test_no_duplicate_ids():
    """Test that all IDs are unique."""
    ids = set()
    duplicates = []
    
    with open('data/processed/faqs_clean.jsonl', 'r', encoding='utf8') as f:
        for line_num, line in enumerate(f, 1):
            obj = json.loads(line.strip())
            record_id = obj.get('id')
            if record_id in ids:
                duplicates.append((line_num, record_id))
            else:
                ids.add(record_id)
    
    assert len(duplicates) == 0, f"Found duplicate IDs: {duplicates[:5]}"

def test_valid_urls():
    """Test that all source URLs are valid."""
    import re
    
    url_pattern = re.compile(r'https?://[^\s/$.?#].[^\s]*')
    invalid_urls = []
    
    with open('data/processed/faqs_clean.jsonl', 'r', encoding='utf8') as f:
        for line_num, line in enumerate(f, 1):
            obj = json.loads(line.strip())
            url = obj.get('source_url', '')
            if not url_pattern.match(url):
                invalid_urls.append((line_num, url))
    
    assert len(invalid_urls) == 0, f"Found invalid URLs: {invalid_urls[:5]}"

def test_valid_date_format():
    """Test that all dates are in YYYY-MM-DD format."""
    import re
    
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    invalid_dates = []
    
    with open('data/processed/faqs_clean.jsonl', 'r', encoding='utf8') as f:
        for line_num, line in enumerate(f, 1):
            obj = json.loads(line.strip())
            date = obj.get('date_fetched', '')
            if not date_pattern.match(date):
                invalid_dates.append((line_num, date))
    
    assert len(invalid_dates) == 0, f"Found invalid dates: {invalid_dates[:5]}"

def test_minimum_text_length():
    """Test that all texts meet minimum length requirements."""
    short_texts = []
    
    with open('data/processed/faqs_clean.jsonl', 'r', encoding='utf8') as f:
        for line_num, line in enumerate(f, 1):
            obj = json.loads(line.strip())
            text = obj.get('text', '')
            if len(text) < 10:
                short_texts.append((line_num, len(text)))
    
    assert len(short_texts) == 0, f"Found texts shorter than 10 chars: {short_texts[:5]}"

def test_no_empty_text_fields():
    """Test that no text fields are empty or just whitespace."""
    empty_texts = []
    
    with open('data/processed/faqs_clean.jsonl', 'r', encoding='utf8') as f:
        for line_num, line in enumerate(f, 1):
            obj = json.loads(line.strip())
            text = obj.get('text', '').strip()
            if not text:
                empty_texts.append(line_num)
    
    assert len(empty_texts) == 0, f"Found empty text fields on lines: {empty_texts[:5]}"

def test_data_quality_metrics():
    """Test basic data quality metrics."""
    df = pd.read_json('data/processed/faqs_clean.jsonl', lines=True)
    
    # Test minimum record count
    assert len(df) > 0, "Dataset is empty"
    
    # Test for missing values in critical fields
    assert df['id'].isnull().sum() == 0, "Found missing IDs"
    assert df['source_url'].isnull().sum() == 0, "Found missing source URLs"
    assert df['text'].isnull().sum() == 0, "Found missing texts"
    assert df['date_fetched'].isnull().sum() == 0, "Found missing dates"
    
    # Test uniqueness
    assert df['id'].nunique() == len(df), "IDs are not unique"
    
    # Test reasonable text length distribution
    text_lengths = df['text'].str.len()
    assert text_lengths.mean() > 20, "Average text length too short"
    assert text_lengths.max() < 10000, "Some texts are extremely long"

def test_region_values():
    """Test that region values are valid if present."""
    valid_regions = {'Antioquia', 'Valle del Cauca', 'Cundinamarca', 'Bogotá', 'Medellín', 'Cali'}
    invalid_regions = set()
    
    with open('data/processed/faqs_clean.jsonl', 'r', encoding='utf8') as f:
        for line_num, line in enumerate(f, 1):
            obj = json.loads(line.strip())
            region = obj.get('region')
            if region and region not in valid_regions:
                invalid_regions.add(region)
    
    # Note: This test can be adjusted based on your actual valid regions
    if invalid_regions:
        print(f"Warning: Found unexpected regions: {invalid_regions}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
