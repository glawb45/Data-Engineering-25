import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import io

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "metadata"))

import pytest
import pandas as pd
from metadata_cleaner import clean_release_date


class TestCleanReleaseDate:
    def test_clean_release_date_with_ebook_suffix(self):
        """Test removing [EBook #xxxx] suffix."""
        input_val = "January 1, 2020 [EBook #12345]"
        result = clean_release_date(input_val)
        assert result == "January 1, 2020"
        assert "[EBook" not in result

    def test_clean_release_date_with_etext_suffix(self):
        """Test removing [Etext #xxxx] suffix."""
        input_val = "December 25, 2019 [Etext #67890]"
        result = clean_release_date(input_val)
        assert result == "December 25, 2019"

    def test_clean_release_date_no_suffix(self):
        """Test that dates without suffix are unchanged."""
        input_val = "March 15, 2021"
        result = clean_release_date(input_val)
        assert result == "March 15, 2021"

    def test_clean_release_date_with_whitespace(self):
        """Test trimming whitespace."""
        input_val = "  April 10, 2020 [EBook #111]  "
        result = clean_release_date(input_val)
        assert result == "April 10, 2020"
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_clean_release_date_nan(self):
        """Test handling NaN values."""
        result = clean_release_date(pd.NA)
        assert pd.isna(result)

        result = clean_release_date(None)
        assert pd.isna(result)

    def test_clean_release_date_empty_string(self):
        """Test handling empty strings."""
        result = clean_release_date("")
        assert result == ""

    def test_clean_release_date_complex_brackets(self):
        """Test with multiple bracket patterns."""
        input_val = "May 5, 2020 [Release Date: May 5, 2020] [EBook #999]"
        result = clean_release_date(input_val)
        # Should only remove the last bracketed section
        assert "[EBook #999]" not in result


class TestDataFrameOperations:
    """Test DataFrame manipulation logic without S3."""

    def test_remove_minus_eight_rows(self):
        """Test removing rows where book_id ends with '-8'."""
        # Create test DataFrame
        df = pd.DataFrame(
            {
                "book_id": ["123-0", "456-8", "789-0", "111-8"],
                "title": ["Book A", "Book B", "Book C", "Book D"],
            }
        )

        # Apply filter
        mask_minus8 = df["book_id"].astype(str).str.endswith("-8")
        df_filtered = df[~mask_minus8]

        # Should have removed 2 rows
        assert len(df_filtered) == 2
        assert "456-8" not in df_filtered["book_id"].values
        assert "111-8" not in df_filtered["book_id"].values

    def test_drop_redundant_columns(self):
        """Test dropping gutenberg_id and language columns."""
        df = pd.DataFrame(
            {
                "book_id": ["123", "456"],
                "gutenberg_id": ["123", "456"],
                "language": ["en", "en"],
                "title": ["Book A", "Book B"],
            }
        )

        # Drop columns
        cols_to_drop = ["gutenberg_id", "language"]
        df_cleaned = df.drop(columns=cols_to_drop)

        # Should not have dropped columns
        assert "gutenberg_id" not in df_cleaned.columns
        assert "language" not in df_cleaned.columns
        assert "book_id" in df_cleaned.columns
        assert "title" in df_cleaned.columns

    def test_apply_clean_release_date(self):
        """Test applying clean_release_date to DataFrame column."""
        df = pd.DataFrame(
            {
                "release_date": [
                    "Jan 1, 2020 [EBook #123]",
                    "Feb 2, 2021",
                    "Mar 3, 2019 [Etext #456]",
                ]
            }
        )

        df["release_date"] = df["release_date"].apply(clean_release_date)

        # Check that brackets are removed
        assert "[EBook" not in df["release_date"].iloc[0]
        assert df["release_date"].iloc[1] == "Feb 2, 2021"
        assert "[Etext" not in df["release_date"].iloc[2]


@patch("metadata_cleaner.s3")
def test_main_integration(mock_s3):
    """Integration test for main function with mocked S3."""
    # Mock CSV data
    mock_csv_data = """book_id,gutenberg_id,title,author,release_date,language
123-0,123,Book A,Author A,Jan 1 2020 [EBook #123],en
456-8,456,Book B,Author B,Feb 2 2021,en
789-0,789,Book C,Author C,Mar 3 2019 [Etext #789],en"""

    # Mock S3 get_object response
    mock_response = {
        "Body": Mock(read=Mock(return_value=mock_csv_data.encode("utf-8")))
    }
    mock_s3.get_object.return_value = mock_response

    # Mock S3 put_object
    mock_s3.put_object.return_value = {}

    # Import and run main
    from metadata_cleaner import main

    # This will run without actual AWS credentials
    main()

    # Verify S3 interactions
    assert mock_s3.get_object.called
    assert mock_s3.put_object.called

    # Get the uploaded data
    put_call_args = mock_s3.put_object.call_args
    uploaded_body = put_call_args[1]["Body"]

    # Parse the uploaded CSV
    df_uploaded = pd.read_csv(io.BytesIO(uploaded_body))

    # Verify cleaning operations
    # Should have removed the row with book_id ending in '-8'
    assert len(df_uploaded) == 2
    assert "456-8" not in df_uploaded["book_id"].values

    # Should have dropped gutenberg_id and language columns
    assert "gutenberg_id" not in df_uploaded.columns
    assert "language" not in df_uploaded.columns


def test_constants():
    """Test that module constants are defined correctly."""
    from metadata_cleaner import REGION, BUCKET, INPUT_KEY, OUTPUT_KEY

    assert REGION == "us-east-1"
    assert isinstance(BUCKET, str)
    assert isinstance(INPUT_KEY, str)
    assert isinstance(OUTPUT_KEY, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
