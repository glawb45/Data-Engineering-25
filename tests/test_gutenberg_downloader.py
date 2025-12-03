#!/usr/bin/env python3
import unittest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
import zipfile
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ingestion.gutenberg_downloader import GutenbergDownloader


class TestGutenbergDownloader(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.bucket_name = "test-bucket"
        self.prefix = "test-prefix"

    @patch('ingestion.gutenberg_downloader.boto3.client')
    def test_init(self, mock_boto_client):
        """Test GutenbergDownloader initialization"""
        downloader = GutenbergDownloader(
            bucket_name=self.bucket_name,
            prefix=self.prefix,
            max_urls=10
        )

        self.assertEqual(downloader.bucket, self.bucket_name)
        self.assertEqual(downloader.prefix, self.prefix)
        self.assertEqual(downloader.file_type, "txt")
        self.assertEqual(downloader.language, "en")
        self.assertEqual(downloader.max_urls, 10)
        mock_boto_client.assert_called_once_with("s3")

    @patch('ingestion.gutenberg_downloader.boto3.client')
    @patch('ingestion.gutenberg_downloader.requests.get')
    def test_get_all_book_urls(self, mock_requests_get, mock_boto_client):
        """Test fetching book URLs"""
        # Mock response with sample URLs
        mock_response = Mock()
        mock_response.text = '''
            <html>
                <a href="https://www.gutenberg.org/files/12345/12345.zip">Book 1</a>
                <a href="/files/67890/67890.zip">Book 2</a>
            </html>
        '''
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        downloader = GutenbergDownloader(
            bucket_name=self.bucket_name,
            max_urls=2
        )

        urls = downloader.get_all_book_urls()

        self.assertEqual(len(urls), 2)
        self.assertIn("https://www.gutenberg.org/files/12345/12345.zip", urls)
        self.assertIn("https://www.gutenberg.org/files/67890/67890.zip", urls)

    @patch('ingestion.gutenberg_downloader.boto3.client')
    def test_upload_to_s3(self, mock_boto_client):
        """Test S3 upload functionality"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        downloader = GutenbergDownloader(bucket_name=self.bucket_name)

        test_content = b"test content"
        test_key = "test/file.txt"

        downloader.upload_to_s3(test_key, test_content)

        mock_s3.upload_fileobj.assert_called_once()
        call_args = mock_s3.upload_fileobj.call_args
        self.assertEqual(call_args[0][1], self.bucket_name)
        self.assertEqual(call_args[0][2], test_key)

    @patch('ingestion.gutenberg_downloader.boto3.client')
    @patch('ingestion.gutenberg_downloader.requests.get')
    def test_download_and_upload_zip(self, mock_requests_get, mock_boto_client):
        """Test downloading and uploading a zip file"""
        # Create a mock zip file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test.txt", "test content")
        zip_content = zip_buffer.getvalue()

        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = zip_content
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        downloader = GutenbergDownloader(bucket_name=self.bucket_name)

        test_url = "https://www.gutenberg.org/files/12345/12345.zip"
        downloader.download_and_upload_zip(test_url)

        # Should upload both raw zip and extracted content
        self.assertGreaterEqual(mock_s3.upload_fileobj.call_count, 2)


if __name__ == '__main__':
    unittest.main()
