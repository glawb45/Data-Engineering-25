import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "metadata"))

import pytest
from metadata_extractor import (
    extract_with_heuristics,
    derive_ids_from_key,
    is_complete_case,
    list_text_files,
    read_snippet_from_s3,
)


class TestExtractWithHeuristics:
    def test_extract_title(self):
        """Test extracting title from header."""
        snippet = """
Title: The Great Adventure
Author: John Doe
Release Date: January 1, 2020
Language: English
"""
        result = extract_with_heuristics(snippet)

        assert result["title"] == "The Great Adventure"

    def test_extract_author(self):
        """Test extracting author from header."""
        snippet = """
Title: Sample Book
Author: Jane Smith
"""
        result = extract_with_heuristics(snippet)

        assert result["author"] == "Jane Smith"

    def test_extract_release_date(self):
        """Test extracting release date."""
        snippet = """
Title: Book
Release Date: March 15, 2021
"""
        result = extract_with_heuristics(snippet)

        assert result["release_date"] == "March 15, 2021"

    def test_extract_language(self):
        """Test extracting language."""
        snippet = """
Title: Book
Language: English
"""
        result = extract_with_heuristics(snippet)

        assert result["language"] == "English"

    def test_extract_all_fields(self):
        """Test extracting all metadata fields."""
        snippet = """
Title: Complete Book
Author: Full Name
Release Date: December 1, 2020
Language: English
"""
        result = extract_with_heuristics(snippet)

        assert result["title"] == "Complete Book"
        assert result["author"] == "Full Name"
        assert result["release_date"] == "December 1, 2020"
        assert result["language"] == "English"

    def test_missing_fields(self):
        """Test handling missing fields."""
        snippet = "Just some random text without headers."
        result = extract_with_heuristics(snippet)

        # All fields should be None
        assert result["title"] is None
        assert result["author"] is None
        assert result["release_date"] is None
        assert result["language"] is None

    def test_case_insensitive_labels(self):
        """Test that labels are case-insensitive."""
        snippet = """
TITLE: Uppercase Title
AUTHOR: Uppercase Author
"""
        result = extract_with_heuristics(snippet)

        assert result["title"] == "Uppercase Title"
        assert result["author"] == "Uppercase Author"

    def test_skip_empty_values(self):
        """Test that empty values are skipped."""
        snippet = """
Title:
Author: Real Author
"""
        result = extract_with_heuristics(snippet)

        # Title should be None (empty value), Author should be set
        assert result["title"] is None
        assert result["author"] == "Real Author"


class TestDeriveIdsFromKey:
    def test_derive_book_id_from_key(self):
        """Test deriving book_id from S3 key path."""
        key = "corpus/extracted/10084-8/10084-8.txt"
        md = {"gutenberg_id": None}

        book_id, gutenberg_id = derive_ids_from_key(key, md)

        assert book_id == "10084-8"

    def test_derive_gutenberg_id_from_filename(self):
        """Test deriving gutenberg_id from filename."""
        key = "corpus/extracted/10084-8/10084-8.txt"
        md = {"gutenberg_id": None}

        book_id, gutenberg_id = derive_ids_from_key(key, md)

        assert gutenberg_id == "10084"

    def test_use_metadata_gutenberg_id(self):
        """Test using gutenberg_id from metadata if available."""
        key = "corpus/extracted/10084-8/10084-8.txt"
        md = {"gutenberg_id": "99999"}

        book_id, gutenberg_id = derive_ids_from_key(key, md)

        # Should use the one from metadata
        assert gutenberg_id == "99999"

    def test_different_key_format(self):
        """Test with different S3 key format."""
        key = "corpus/extracted/123-0/123-0.txt"
        md = {"gutenberg_id": None}

        book_id, gutenberg_id = derive_ids_from_key(key, md)

        assert book_id == "123-0"
        assert gutenberg_id == "123"

    def test_short_key_path(self):
        """Test handling short key paths."""
        key = "file.txt"
        md = {"gutenberg_id": None}

        book_id, gutenberg_id = derive_ids_from_key(key, md)

        # book_id might be None if path is too short
        # Just ensure no error is raised
        assert isinstance(book_id, (str, type(None)))


class TestIsCompleteCase:
    def test_complete_case(self):
        """Test that complete row is recognized."""
        row = {
            "title": "Book Title",
            "author": "Author Name",
            "release_date": "Jan 1, 2020",
            "language": "English",
            "gutenberg_id": "12345",
        }

        assert is_complete_case(row) is True

    def test_missing_title(self):
        """Test incomplete case with missing title."""
        row = {
            "title": None,
            "author": "Author Name",
            "release_date": "Jan 1, 2020",
            "language": "English",
            "gutenberg_id": "12345",
        }

        assert is_complete_case(row) is False

    def test_missing_author(self):
        """Test incomplete case with missing author."""
        row = {
            "title": "Book Title",
            "author": None,
            "release_date": "Jan 1, 2020",
            "language": "English",
            "gutenberg_id": "12345",
        }

        assert is_complete_case(row) is False

    def test_empty_string_field(self):
        """Test that empty string counts as missing."""
        row = {
            "title": "Book Title",
            "author": "",
            "release_date": "Jan 1, 2020",
            "language": "English",
            "gutenberg_id": "12345",
        }

        assert is_complete_case(row) is False

    def test_whitespace_only_field(self):
        """Test that whitespace-only string counts as missing."""
        row = {
            "title": "Book Title",
            "author": "Author Name",
            "release_date": "   ",
            "language": "English",
            "gutenberg_id": "12345",
        }

        assert is_complete_case(row) is False

    def test_all_fields_present(self):
        """Test with all required fields present."""
        row = {
            "title": "T",
            "author": "A",
            "release_date": "D",
            "language": "L",
            "gutenberg_id": "1",
        }

        assert is_complete_case(row) is True


@patch("metadata_extractor.s3")
def test_list_text_files(mock_s3):
    """Test listing text files from S3."""
    # Mock paginator
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator

    # Mock pagination results
    mock_paginator.paginate.return_value = [
        {
            "Contents": [
                {"Key": "corpus/extracted/123/123.txt"},
                {"Key": "corpus/extracted/456/456.txt"},
                {"Key": "corpus/extracted/789/789.pdf"},  # Not a .txt file
            ]
        }
    ]

    # Test the function
    result = list(list_text_files())

    # Should only return .txt files
    assert len(result) == 2
    assert "corpus/extracted/123/123.txt" in result
    assert "corpus/extracted/456/456.txt" in result
    assert "corpus/extracted/789/789.pdf" not in result


@patch("metadata_extractor.s3")
def test_read_snippet_from_s3(mock_s3):
    """Test reading snippet from S3."""
    # Mock S3 response
    test_content = "This is a test file content " * 100  # Long content
    mock_body = Mock()
    mock_body.read.return_value = test_content.encode("utf-8")

    mock_s3.get_object.return_value = {"Body": mock_body}

    # Read snippet
    snippet = read_snippet_from_s3("test/file.txt", max_chars=50)

    # Should be truncated to max_chars
    assert len(snippet) == 50
    assert snippet == test_content[:50]


def test_constants():
    """Test that module constants are defined correctly."""
    from metadata_extractor import (
        REGION,
        BUCKET,
        INPUT_PREFIX,
        OUTPUT_KEY,
        MODEL_ID,
        MAX_CHARS,
    )

    assert REGION == "us-east-1"
    assert isinstance(BUCKET, str)
    assert isinstance(INPUT_PREFIX, str)
    assert isinstance(OUTPUT_KEY, str)
    assert isinstance(MODEL_ID, str)
    assert isinstance(MAX_CHARS, int)
    assert MAX_CHARS > 0


class TestBedrockIntegration:
    """Tests for Bedrock-related functionality."""

    @patch("metadata_extractor.bedrock")
    def test_extract_with_bedrock_success(self, mock_bedrock):
        """Test successful metadata extraction with Bedrock."""
        from metadata_extractor import extract_with_bedrock

        # Mock Bedrock response
        mock_response = {
            "body": Mock(
                read=Mock(
                    return_value=json.dumps(
                        {
                            "content": [
                                {
                                    "text": json.dumps(
                                        {
                                            "title": "Book Title",
                                            "author": "Author Name",
                                            "release_date": "Jan 1, 2020",
                                            "language": "English",
                                            "gutenberg_id": "12345",
                                        }
                                    )
                                }
                            ]
                        }
                    ).encode()
                )
            )
        }
        mock_bedrock.invoke_model.return_value = mock_response

        snippet = "Sample book header text"
        result = extract_with_bedrock(snippet)

        # Verify result
        assert result["title"] == "Book Title"
        assert result["author"] == "Author Name"

    @patch("metadata_extractor.bedrock")
    def test_extract_with_bedrock_invalid_json(self, mock_bedrock):
        """Test Bedrock with invalid JSON response."""
        from metadata_extractor import extract_with_bedrock

        # Mock Bedrock response with invalid JSON
        mock_response = {
            "body": Mock(
                read=Mock(
                    return_value=json.dumps(
                        {"content": [{"text": "Not valid JSON"}]}
                    ).encode()
                )
            )
        }
        mock_bedrock.invoke_model.return_value = mock_response

        snippet = "Sample text"
        result = extract_with_bedrock(snippet)

        # Should return all None values when JSON parsing fails
        assert result["title"] is None
        assert result["author"] is None
        assert result["release_date"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
