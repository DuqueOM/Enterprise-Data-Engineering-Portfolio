"""Test data schema validation."""
import pandas as pd
import os

def test_sample_data_exists():
    """Test that sample data file exists and has correct format."""
    data_path = 'data/sample.csv'
    assert os.path.exists(data_path), f"Sample data file {data_path} does not exist"
    
    df = pd.read_csv(data_path)
    assert 'text' in df.columns, "Missing 'text' column in sample data"
    assert 'label' in df.columns, "Missing 'label' column in sample data"
    assert len(df) > 0, "Sample data is empty"
    assert df['label'].isin([0, 1]).all(), "Labels should be binary (0 or 1)"

def test_data_quality():
    """Test basic data quality checks."""
    data_path = 'data/sample.csv'
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        assert df['text'].str.len().min() > 0, "Text entries should not be empty"
        assert df.isnull().sum().sum() == 0, "Data should not contain null values"
