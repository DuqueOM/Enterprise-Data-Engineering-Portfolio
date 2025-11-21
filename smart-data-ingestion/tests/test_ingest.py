#!/usr/bin/env python3
"""
Unit tests for the ingestion module.

Tests cover:
- HTML fetching with retry logic
- HTML parsing and chunking
- JSONL file generation
- Error handling
"""

import json

# Import functions from the module
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.ingest import (
    create_session,
    fetch_page,
    parse_html_to_chunks,
    process_urls,
    save_chunks_to_jsonl,
)


class TestSessionCreation:
    """Test session creation with retry logic."""

    def test_create_session_returns_session(self):
        """Test that create_session returns a requests.Session object."""
        session = create_session()
        assert isinstance(session, requests.Session)

    def test_create_session_has_retry_adapters(self):
        """Test that session has retry adapters mounted."""
        session = create_session()
        assert "http://" in session.adapters
        assert "https://" in session.adapters


class TestFetchPage:
    """Test web page fetching functionality."""

    @patch("scripts.ingest.create_session")
    def test_fetch_page_success(self, mock_create_session):
        """Test successful page fetch."""
        # Mock response
        mock_response = Mock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.status_code = 200
        mock_response.apparent_encoding = "utf-8"

        # Mock session
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_create_session.return_value = mock_session

        # Test fetch
        html = fetch_page("https://example.com")

        assert html == "<html><body>Test content</body></html>"
        mock_session.get.assert_called_once()

    @patch("scripts.ingest.create_session")
    def test_fetch_page_timeout(self, mock_create_session):
        """Test fetch with timeout error."""
        mock_session = Mock()
        mock_session.get.side_effect = requests.Timeout("Connection timeout")
        mock_create_session.return_value = mock_session

        with pytest.raises(requests.Timeout):
            fetch_page("https://example.com", timeout=1)

    @patch("scripts.ingest.create_session")
    def test_fetch_page_http_error(self, mock_create_session):
        """Test fetch with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_create_session.return_value = mock_session

        with pytest.raises(requests.HTTPError):
            fetch_page("https://example.com/notfound")


class TestParseHtmlToChunks:
    """Test HTML parsing and text chunking."""

    def test_parse_simple_html(self):
        """Test parsing of simple HTML."""
        html = """
        <html>
            <body>
                <p>First paragraph with some content.</p>
                <p>Second paragraph with more content.</p>
            </body>
        </html>
        """

        chunks = parse_html_to_chunks(
            html, "https://test.com", "Test Region", chunk_size_chars=100
        )

        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("id" in chunk for chunk in chunks)
        assert all(chunk["region"] == "Test Region" for chunk in chunks)

    def test_parse_html_with_headers(self):
        """Test parsing HTML with headers."""
        html = """
        <html>
            <body>
                <h2>Section Header</h2>
                <p>Paragraph content under header.</p>
                <h3>Subsection</h3>
                <p>More content here.</p>
            </body>
        </html>
        """

        chunks = parse_html_to_chunks(
            html, "https://test.com", "Test", chunk_size_chars=50
        )

        assert len(chunks) > 0
        # Check that text contains header content
        all_text = " ".join(chunk["text"] for chunk in chunks)
        assert "Section Header" in all_text

    def test_parse_empty_html(self):
        """Test parsing of HTML with no extractable text."""
        html = "<html><body></body></html>"

        chunks = parse_html_to_chunks(html, "https://test.com", "Test")

        assert chunks == []

    def test_chunk_size_respected(self):
        """Test that chunks respect maximum size."""
        # Create long text
        long_text = " ".join(["word"] * 1000)
        html = f"<html><body><p>{long_text}</p></body></html>"

        chunk_size = 500
        chunks = parse_html_to_chunks(
            html, "https://test.com", "Test", chunk_size_chars=chunk_size
        )

        # Check that no chunk exceeds the size (with some tolerance for word boundaries)
        for chunk in chunks:
            assert (
                len(chunk["text"]) <= chunk_size + 100
            )  # Allow some overflow for word completion

    def test_chunk_metadata(self):
        """Test that chunks contain required metadata."""
        html = "<html><body><p>Test content</p></body></html>"

        chunks = parse_html_to_chunks(html, "https://test.com", "Test Region")

        assert len(chunks) > 0
        chunk = chunks[0]

        # Check all required fields
        assert "id" in chunk
        assert "source_url" in chunk
        assert "region" in chunk
        assert "text" in chunk
        assert "date_fetched" in chunk
        assert "chunk_index" in chunk
        assert "total_chars" in chunk

        # Verify values
        assert chunk["source_url"] == "https://test.com"
        assert chunk["region"] == "Test Region"
        assert len(chunk["id"]) == 12  # SHA1 hash truncated to 12 chars


class TestSaveChunksToJsonl:
    """Test JSONL file saving."""

    def test_save_chunks_creates_file(self):
        """Test that save_chunks_to_jsonl creates output file."""
        chunks = [
            {"id": "test1", "text": "Chunk 1"},
            {"id": "test2", "text": "Chunk 2"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.jsonl"
            save_chunks_to_jsonl(chunks, str(output_path))

            assert output_path.exists()

            # Verify content
            with open(output_path, "r") as f:
                lines = f.readlines()

            assert len(lines) == 2

            # Parse and verify
            loaded_chunks = [json.loads(line) for line in lines]
            assert loaded_chunks[0]["id"] == "test1"
            assert loaded_chunks[1]["id"] == "test2"

    def test_save_chunks_creates_parent_dirs(self):
        """Test that parent directories are created if they don't exist."""
        chunks = [{"id": "test", "text": "Content"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "output.jsonl"
            save_chunks_to_jsonl(chunks, str(output_path))

            assert output_path.exists()
            assert output_path.parent.exists()

    def test_save_empty_chunks(self):
        """Test saving empty chunk list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.jsonl"
            save_chunks_to_jsonl([], str(output_path))

            assert output_path.exists()

            with open(output_path, "r") as f:
                content = f.read()

            assert content == ""


class TestProcessUrls:
    """Test URL processing pipeline."""

    @patch("scripts.ingest.fetch_page")
    def test_process_multiple_urls(self, mock_fetch_page):
        """Test processing multiple URLs."""
        # Mock responses
        mock_fetch_page.side_effect = [
            "<html><body><p>Content from URL 1</p></body></html>",
            "<html><body><p>Content from URL 2</p></body></html>",
        ]

        urls = [
            ("https://example1.com", "Region1"),
            ("https://example2.com", "Region2"),
        ]

        chunks = process_urls(urls, chunk_size=100)

        assert len(chunks) >= 2
        assert any(chunk["source_url"] == "https://example1.com" for chunk in chunks)
        assert any(chunk["source_url"] == "https://example2.com" for chunk in chunks)

    @patch("scripts.ingest.fetch_page")
    def test_process_urls_with_failures(self, mock_fetch_page):
        """Test that processing continues when some URLs fail."""
        # First URL fails, second succeeds
        mock_fetch_page.side_effect = [
            requests.RequestException("Failed to fetch"),
            "<html><body><p>Success content</p></body></html>",
        ]

        urls = [("https://fail.com", "Region1"), ("https://success.com", "Region2")]

        chunks = process_urls(urls, chunk_size=100)

        # Should have chunks from the successful URL
        assert len(chunks) >= 1
        assert all(chunk["source_url"] == "https://success.com" for chunk in chunks)


# Integration tests
class TestIntegration:
    """Integration tests for the complete pipeline."""

    @patch("scripts.ingest.fetch_page")
    def test_full_pipeline(self, mock_fetch_page):
        """Test the complete ingestion pipeline."""
        # Mock HTML response
        html = """
        <html>
            <body>
                <h2>Government FAQ</h2>
                <p>Question 1: How do I register a business?</p>
                <p>Answer: You need to visit the chamber of commerce.</p>
                <p>Question 2: What documents are required?</p>
                <p>Answer: You need ID, address proof, and tax registration.</p>
            </body>
        </html>
        """
        mock_fetch_page.return_value = html

        # Process URLs
        urls = [("https://gov.example.com/faq", "Test Region")]
        chunks = process_urls(urls, chunk_size=200)

        # Save to file
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.jsonl"
            save_chunks_to_jsonl(chunks, str(output_path))

            # Verify file exists and contains data
            assert output_path.exists()

            with open(output_path, "r") as f:
                lines = f.readlines()

            assert len(lines) > 0

            # Verify structure
            for line in lines:
                chunk = json.loads(line)
                assert "id" in chunk
                assert "text" in chunk
                assert "region" in chunk
                assert chunk["region"] == "Test Region"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
