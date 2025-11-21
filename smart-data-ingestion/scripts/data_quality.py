#!/usr/bin/env python3
"""
Data quality analysis script for PYME QA dataset.
Generates comprehensive quality reports and metrics.
"""
import json
import pandas as pd
from pathlib import Path
import logging
from collections import Counter

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_text_statistics(df):
    """Compute detailed text statistics."""
    stats = {}
    
    # Basic text statistics
    text_lengths = df['text'].str.len()
    stats['text_length'] = {
        'mean': float(text_lengths.mean()),
        'median': float(text_lengths.median()),
        'std': float(text_lengths.std()),
        'min': int(text_lengths.min()),
        'max': int(text_lengths.max()),
        'q25': float(text_lengths.quantile(0.25)),
        'q75': float(text_lengths.quantile(0.75))
    }
    
    # Word count statistics
    word_counts = df['text'].str.split().str.len()
    stats['word_count'] = {
        'mean': float(word_counts.mean()),
        'median': float(word_counts.median()),
        'std': float(word_counts.std()),
        'min': int(word_counts.min()),
        'max': int(word_counts.max())
    }
    
    # Language detection (simple heuristic)
    spanish_words = ['que', 'la', 'de', 'y', 'en', 'el', 'los', 'del', 'se', 'las', 'por', 'un', 'para', 'con', 'no', 'una', 'su', 'al', 'lo', 'como']
    english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been']
    
    def detect_language(text):
        words = text.lower().split()
        spanish_count = sum(1 for word in words if word in spanish_words)
        english_count = sum(1 for word in words if word in english_words)
        return 'spanish' if spanish_count > english_count else 'english' if english_count > spanish_count else 'unknown'
    
    languages = df['text'].apply(detect_language)
    stats['language_distribution'] = dict(Counter(languages))
    
    return stats

def compute_data_quality_metrics(df):
    """Compute data quality metrics."""
    metrics = {}
    
    # Completeness metrics
    metrics['completeness'] = {
        'total_records': len(df),
        'missing_values': df.isnull().sum().to_dict(),
        'completeness_rate': float((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100)
    }
    
    # Uniqueness metrics
    metrics['uniqueness'] = {
        'duplicate_rows': int(df.duplicated().sum()),
        'duplicate_texts': int(df.duplicated(subset=['text']).sum()),
        'unique_sources': int(df['source_url'].nunique()),
        'unique_ids': int(df['id'].nunique())
    }
    
    # Consistency metrics
    metrics['consistency'] = {
        'invalid_urls': int(~df['source_url'].str.match(r'https?://.*', na=False).sum()),
        'invalid_dates': int(~df['date_fetched'].str.match(r'\d{4}-\d{2}-\d{2}', na=False).sum()),
        'invalid_ids': int(df['id'].str.len() == 0).sum()
    }
    
    # Text quality metrics
    metrics['text_quality'] = {
        'very_short_texts': int((df['text'].str.len() < 50).sum()),
        'empty_texts': int((df['text'].str.strip() == '').sum()),
        'texts_with_special_chars': int(df['text'].str.contains(r'[^\w\s\u00C0-\u00FF]', regex=True).sum()),
        'texts_with_numbers': int(df['text'].str.contains(r'\d', regex=True).sum())
    }
    
    return metrics

def generate_html_report(df, text_stats, quality_metrics, output_path):
    """Generate HTML quality report."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PYME QA Dataset Quality Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            .metric {{ margin: 10px 0; }}
            .good {{ color: green; }}
            .warning {{ color: orange; }}
            .error {{ color: red; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>PYME QA Dataset Quality Report</h1>
            <p>Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>Dataset Overview</h2>
            <div class="metric"><strong>Total Records:</strong> {len(df)}</div>
            <div class="metric"><strong>Columns:</strong> {len(df.columns)}</div>
            <div class="metric"><strong>Unique Sources:</strong> {df['source_url'].nunique()}</div>
            <div class="metric"><strong>Regions:</strong> {', '.join(df['region'].dropna().unique())}</div>
        </div>
        
        <div class="section">
            <h2>Text Statistics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Average Text Length</td><td>{text_stats['text_length']['mean']:.1f} chars</td></tr>
                <tr><td>Median Text Length</td><td>{text_stats['text_length']['median']:.1f} chars</td></tr>
                <tr><td>Average Word Count</td><td>{text_stats['word_count']['mean']:.1f} words</td></tr>
                <tr><td>Median Word Count</td><td>{text_stats['word_count']['median']:.1f} words</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>Data Quality Metrics</h2>
            <div class="metric {'good' if quality_metrics['completeness']['completeness_rate'] > 95 else 'warning' if quality_metrics['completeness']['completeness_rate'] > 85 else 'error'}">
                <strong>Completeness Rate:</strong> {quality_metrics['completeness']['completeness_rate']:.1f}%
            </div>
            <div class="metric {'good' if quality_metrics['uniqueness']['duplicate_texts'] == 0 else 'warning' if quality_metrics['uniqueness']['duplicate_texts'] < 5 else 'error'}">
                <strong>Duplicate Texts:</strong> {quality_metrics['uniqueness']['duplicate_texts']}
            </div>
            <div class="metric {'good' if quality_metrics['text_quality']['very_short_texts'] == 0 else 'warning'}">
                <strong>Very Short Texts (&lt;50 chars):</strong> {quality_metrics['text_quality']['very_short_texts']}
            </div>
        </div>
        
        <div class="section">
            <h2>Language Distribution</h2>
            <table>
                <tr><th>Language</th><th>Count</th><th>Percentage</th></tr>
    """
    
    for lang, count in text_stats['language_distribution'].items():
        percentage = (count / len(df)) * 100
        html_content += f"<tr><td>{lang}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
    
    html_content += """
            </table>
        </div>
        
        <div class="section">
            <h2>Recommendations</h2>
    """
    
    # Add recommendations based on quality metrics
    if quality_metrics['uniqueness']['duplicate_texts'] > 0:
        html_content += "<p class='warning'>⚠️ Consider removing duplicate text entries to improve data quality.</p>"
    
    if quality_metrics['text_quality']['very_short_texts'] > 0:
        html_content += "<p class='warning'>⚠️ Some texts are very short. Consider filtering or expanding them.</p>"
    
    if quality_metrics['consistency']['invalid_urls'] > 0:
        html_content += "<p class='error'>❌ Invalid URLs found. Please review source URLs.</p>"
    
    if quality_metrics['completeness']['completeness_rate'] < 95:
        html_content += "<p class='warning'>⚠️ Data completeness is below 95%. Check for missing values.</p>"
    
    if quality_metrics['uniqueness']['duplicate_texts'] == 0 and quality_metrics['text_quality']['very_short_texts'] == 0:
        html_content += "<p class='good'>✅ Data quality looks good! No major issues detected.</p>"
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"HTML report generated: {output_path}")

def main():
    """Main function to run data quality analysis."""
    input_file = "data/processed/faqs_clean.jsonl"
    output_dir = Path("reports")
    metrics_dir = Path("metrics")
    
    # Create directories
    output_dir.mkdir(exist_ok=True)
    metrics_dir.mkdir(exist_ok=True)
    
    # Load data
    logger.info(f"Loading data from {input_file}")
    df = pd.read_json(input_file, lines=True)
    
    # Compute metrics
    logger.info("Computing text statistics...")
    text_stats = compute_text_statistics(df)
    
    logger.info("Computing data quality metrics...")
    quality_metrics = compute_data_quality_metrics(df)
    
    # Generate HTML report
    html_output = output_dir / "quality_report.html"
    generate_html_report(df, text_stats, quality_metrics, html_output)
    
    # Save metrics as JSON
    metrics_output = metrics_dir / "quality.json"
    all_metrics = {
        "text_statistics": text_stats,
        "data_quality": quality_metrics,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(metrics_output, 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Metrics saved to {metrics_output}")
    logger.info("🎉 Data quality analysis completed!")

if __name__ == "__main__":
    main()
