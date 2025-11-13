#!/usr/bin/env python3
"""
Project Gutenberg Complete Corpus Downloader
Downloads all books from Project Gutenberg using their harvest API
"""

import requests
import time
import os
import zipfile
from pathlib import Path
from urllib.parse import urlparse
import re

class GutenbergDownloader:
    def __init__(self, output_dir="gutenberg_corpus", file_type="txt", language="en"):
        """
        Initialize the downloader
        
        Args:
            output_dir: Directory to save downloaded books
            file_type: Type of files to download (txt, html, epub.images, etc.)
            language: Language code (en, de, fr, etc.)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.file_type = file_type
        self.language = language
        self.base_url = "http://www.gutenberg.org/robot/harvest"
        self.downloaded_count = 0
        self.failed_count = 0
        
    def get_all_book_urls(self):
        """Fetch all book URLs from the harvest API"""
        all_urls = []
        offset = 0
        
        print("Fetching book URLs from Project Gutenberg...")
        
        while True:
            params = {
                'filetypes[]': self.file_type,
                'langs[]': self.language,
                'offset': offset
            }
            
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                # Extract URLs from response
                urls = re.findall(r'http://[^\s<>"]+\.zip', response.text)
                
                if not urls:
                    print(f"No more URLs found. Total URLs collected: {len(all_urls)}")
                    break
                
                all_urls.extend(urls)
                print(f"Collected {len(all_urls)} URLs so far...")
                
                # Check if there's a "Next Page" indicator
                if "Next Page" not in response.text:
                    break
                
                # Increment offset (typically by 100)
                offset += len(urls)
                
                # Be respectful - wait between requests
                time.sleep(2)
                
            except Exception as e:
                print(f"Error fetching URLs at offset {offset}: {e}")
                break
        
        return all_urls
    
    def download_file(self, url, retries=3):
        """Download a single file with retry logic"""
        filename = url.split('/')[-1]
        book_id = filename.replace('.zip', '').replace(f'-{self.file_type[0]}', '')
        output_path = self.output_dir / filename
        
        # Skip if already downloaded
        if output_path.exists():
            return True
        
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=30, stream=True)
                response.raise_for_status()
                
                # Download with progress
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.downloaded_count += 1
                return True
                
            except Exception as e:
                if attempt == retries - 1:
                    print(f"Failed to download {filename}: {e}")
                    self.failed_count += 1
                    return False
                time.sleep(2)
        
        return False
    
    def extract_all_zips(self):
        """Extract all downloaded zip files"""
        print("\nExtracting downloaded files...")
        extracted_dir = self.output_dir / "extracted"
        extracted_dir.mkdir(exist_ok=True)
        
        for zip_file in self.output_dir.glob("*.zip"):
            try:
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(extracted_dir / zip_file.stem)
                print(f"Extracted {zip_file.name}")
            except Exception as e:
                print(f"Failed to extract {zip_file.name}: {e}")
    
    def download_corpus(self, extract=True, max_books=None):
        """Download the entire corpus"""
        print(f"Starting Project Gutenberg {self.language.upper()} corpus download")
        print(f"File type: {self.file_type}")
        print(f"Output directory: {self.output_dir}")
        print("-" * 60)
        
        # Get all URLs
        urls = self.get_all_book_urls()
        
        if max_books:
            urls = urls[:max_books]
        
        print(f"\nStarting download of {len(urls)} books...")
        
        # Download all files
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Downloading {url.split('/')[-1]}...", end='\r')
            self.download_file(url)
            
            # Be respectful - wait between downloads
            time.sleep(2)
            
            # Progress update every 50 books
            if i % 50 == 0:
                print(f"\nProgress: {i}/{len(urls)} downloaded, {self.failed_count} failed")
        
        print(f"\n\nDownload complete!")
        print(f"Successfully downloaded: {self.downloaded_count}")
        print(f"Failed: {self.failed_count}")
        
        # Extract if requested
        if extract:
            self.extract_all_zips()
        
        return self.downloaded_count, self.failed_count


def main():
    """Main function with example usage"""
    
    # Configuration
    OUTPUT_DIR = "gutenberg_corpus"
    FILE_TYPE = "txt"  # Options: txt, html, epub.images, epub.noimages, etc.
    LANGUAGE = "en"    # Options: en, de, fr, es, etc.
    
    # Create downloader
    downloader = GutenbergDownloader(
        output_dir=OUTPUT_DIR,
        file_type=FILE_TYPE,
        language=LANGUAGE
    )
    
    # Download corpus
    # Set max_books=100 for testing, remove it to download everything
    downloader.download_corpus(extract=True, max_books=None)


if __name__ == "__main__":
    main()