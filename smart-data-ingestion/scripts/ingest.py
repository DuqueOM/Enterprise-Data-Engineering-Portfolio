#!/usr/bin/env python3
"""
Web Content Ingestion Module

This module provides functionality to scrape web content, parse HTML,
and generate structured JSONL datasets for NLP tasks.

Author: Portfolio Team
License: MIT
"""

import argparse
import hashlib
import json
import logging
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 15
DEFAULT_CHUNK_SIZE = 1500
DEFAULT_REGION = "Antioquia"
DEFAULT_OUTPUT = "data/processed/faqs.jsonl"
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5


def create_session() -> requests.Session:
    """
    Create a requests session with retry logic.

    Returns:
        requests.Session: Configured session with retry mechanism
    """
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_page(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    session: requests.Session | None = None,
) -> str:
    """
    Download the HTML content of a web page.

    Args:
        url: Target URL to fetch
        timeout: Request timeout in seconds
        session: Optional requests session for connection pooling

    Returns:
        str: HTML content of the page

    Raises:
        requests.HTTPError: If the request fails with non-2xx status
        requests.Timeout: If the request exceeds timeout
        requests.RequestException: For other request-related errors

    Example:
        >>> html = fetch_page("https://example.com", timeout=10)
        >>> "Example Domain" in html
        True
    """
    if session is None:
        session = create_session()

    headers = {
        "User-Agent": "Smart-Data-Ingestion-Bot/1.0 (+https://github.com/yourusername/portfolio)"
    }

    logger.info(f"Fetching URL: {url}")

    try:
        response = session.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"

        logger.info(f"Successfully fetched {len(response.text)} characters from {url}")
        return response.text

    except requests.Timeout:
        logger.error(f"Timeout while fetching {url}")
        raise
    except requests.HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code} for {url}")
        raise
    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        raise


def parse_html_to_chunks(
    html: str, url: str, region: str, chunk_size_chars: int = DEFAULT_CHUNK_SIZE
) -> list[dict[str, str]]:
    """
    Parse HTML content and split into text chunks.

    This function extracts text from HTML elements (paragraphs, headers, lists),
    combines them, and splits into fixed-size chunks suitable for NLP processing.

    Args:
        html: Raw HTML content
        url: Source URL (used for generating unique IDs)
        region: Geographic region identifier
        chunk_size_chars: Maximum characters per chunk

    Returns:
        List of dictionaries, each containing:
            - id: Unique identifier (SHA1 hash)
            - source_url: Original URL
            - region: Geographic region
            - text: Extracted text chunk
            - date_fetched: ISO format date

    Example:
        >>> html = "<p>Test paragraph</p>"
        >>> chunks = parse_html_to_chunks(html, "https://test.com", "Test Region")
        >>> len(chunks) >= 1
        True
        >>> "text" in chunks[0] and "id" in chunks[0]
        True
    """
    soup = BeautifulSoup(html, "html.parser")

    # Extract text from relevant HTML elements
    texts = [
        element.get_text(" ", strip=True)
        for element in soup.select("p, h2, h3, li, dd, dt")
        if element.get_text(strip=True)
    ]

    if not texts:
        logger.warning(f"No text content extracted from {url}")
        return []

    combined = "\n".join(texts)
    chunks = []

    # Split into chunks with overlap to preserve context
    for i in range(0, len(combined), chunk_size_chars):
        chunk_text = combined[i : i + chunk_size_chars].strip()

        if not chunk_text or len(chunk_text) < 50:  # Skip very small chunks
            continue

        # Generate stable unique ID
        chunk_id = hashlib.sha256(f"{url}:{i}".encode()).hexdigest()[:12]

        chunks.append(
            {
                "id": chunk_id,
                "source_url": url,
                "region": region,
                "text": chunk_text,
                "date_fetched": time.strftime("%Y-%m-%d"),
                "chunk_index": len(chunks),
                "total_chars": len(chunk_text),
            }
        )

    logger.info(f"Generated {len(chunks)} chunks from {url}")
    return chunks


def save_chunks_to_jsonl(chunks: list[dict[str, str]], output_path: str) -> None:
    """
    Save chunks to JSONL (JSON Lines) format.

    Args:
        chunks: List of chunk dictionaries
        output_path: Path to output JSONL file

    Raises:
        IOError: If file cannot be written
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path_obj, "w", encoding="utf-8") as f:
            for chunk in chunks:
                json_line = json.dumps(chunk, ensure_ascii=False)
                f.write(json_line + "\n")

        logger.info(f"Successfully wrote {len(chunks)} chunks to {output_path}")

    except OSError as e:
        logger.error(f"Failed to write to {output_path}: {e}")
        raise


def process_urls(
    urls: list[tuple[str, str]],
    chunk_size: int,
    session: requests.Session | None = None,
) -> list[dict[str, str]]:
    """
    Process multiple URLs and extract chunks.

    Args:
        urls: List of (url, region) tuples
        chunk_size: Size of text chunks in characters
        session: Optional requests session

    Returns:
        List of all extracted chunks
    """
    all_chunks = []

    if session is None:
        session = create_session()

    for url, region in urls:
        try:
            html = fetch_page(url, session=session)
            chunks = parse_html_to_chunks(html, url, region, chunk_size)
            all_chunks.extend(chunks)

        except requests.RequestException as e:
            logger.error(f"Failed to process {url}: {e}")
            continue
        except Exception as e:
            logger.exception(f"Unexpected error processing {url}: {e}")
            continue

    return all_chunks


def main() -> int:
    """
    Main entry point for the ingestion script.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Ingest web content and generate structured JSONL dataset",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--output", type=str, default=DEFAULT_OUTPUT, help="Output JSONL file path"
    )

    parser.add_argument(
        "--region",
        type=str,
        default=DEFAULT_REGION,
        help="Default geographic region for URLs",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Text chunk size in characters",
    )

    parser.add_argument(
        "--urls-file",
        type=str,
        help="Path to file containing URLs (one per line, format: url,region)",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Load URLs
    if args.urls_file:
        try:
            with open(args.urls_file) as f:
                urls = []
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split(",")
                    url = parts[0].strip()
                    region = parts[1].strip() if len(parts) > 1 else args.region
                    urls.append((url, region))
        except OSError as e:
            logger.error(f"Failed to read URLs file: {e}")
            return 1
    else:
        # Default example URL
        urls = [
            ("https://example.gov/faq", args.region),
        ]
        logger.warning("No URLs file provided, using default example URL")

    if not urls:
        logger.error("No URLs to process")
        return 1

    logger.info(f"Processing {len(urls)} URLs with chunk size {args.chunk_size}")

    try:
        # Process all URLs
        chunks = process_urls(urls, args.chunk_size)

        if not chunks:
            logger.warning("No chunks generated from any URL")
            return 1

        # Save results
        save_chunks_to_jsonl(chunks, args.output)

        # Summary statistics
        total_chars = sum(chunk.get("total_chars", 0) for chunk in chunks)
        logger.info(f"Summary: {len(chunks)} chunks, {total_chars:,} total characters")

        return 0

    except Exception as e:
        logger.exception(f"Fatal error during processing: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
