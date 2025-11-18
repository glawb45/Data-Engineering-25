#!/usr/bin/env python3
import requests
import time
import os
import zipfile
from pathlib import Path
from urllib.parse import urlparse
import re
import boto3
from io import BytesIO

class GutenbergDownloader:
    def __init__(self, bucket_name, prefix="gutenberg", file_type="txt", language="en", max_urls=600):
        self.bucket = bucket_name
        self.prefix = prefix
        self.file_type = file_type
        self.language = language
        self.max_urls = max_urls
        self.base_url = "http://www.gutenberg.org/robot/harvest"
        self.s3 = boto3.client("s3")

    def upload_to_s3(self, key, content_bytes):
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content_bytes
        )
        print(f"Uploaded to s3://{self.bucket}/{key}")

    def get_all_book_urls(self):
        urls = []
        offset = 0
        
        print(f"Fetching up to {self.max_urls} URLs...")

        while len(urls) < self.max_urls:
            params = {
                'filetypes[]': self.file_type,
                'langs[]': self.language,
                'offset': offset,
            }

            resp = requests.get(self.base_url, params=params)
            resp.raise_for_status()

            found = re.findall(r'http://[^\s<>"]+\.zip', resp.text)

            if not found:
                break

            remaining = self.max_urls - len(urls)
            urls.extend(found[:remaining])

            if len(urls) >= self.max_urls:
                break

            offset += len(found)
            time.sleep(1)

        return urls

    def download_and_upload_zip(self, url):
        filename = url.split("/")[-1]
        book_id = filename.replace(".zip", "")

        print(f"Downloading {filename}...")

        resp = requests.get(url, stream=True)
        resp.raise_for_status()

        zip_bytes = resp.content

        # Upload raw ZIP to S3
        self.upload_to_s3(f"{self.prefix}/raw/{filename}", zip_bytes)

        # Extract ZIP in memory
        zip_stream = BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_stream, "r") as z:
            for member in z.namelist():
                extracted = z.read(member)
                s3_key = f"{self.prefix}/extracted/{book_id}/{member}"

                self.upload_to_s3(s3_key, extracted)

    def run(self):
        print("Starting Early-English Gutenberg downloader...")

        urls = self.get_all_book_urls()
        print(f"Found {len(urls)} URLs")

        for i, url in enumerate(urls, start=1):
            print(f"[{i}/{len(urls)}] Processing {url}")
            try:
                self.download_and_upload_zip(url)
            except Exception as e:
                print(f"Failed {url}: {e}")

            time.sleep(1)

        print("Done!")


def main():
    downloader = GutenbergDownloader(
        bucket_name="gutenberg-early-english-corpus",
        prefix="corpus",
        file_type="txt",
        language="en",
        max_urls=600
    )

    downloader.run()


if __name__ == "__main__":
    main()
