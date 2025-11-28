#!/usr/bin/env python3
import requests
import time
import re
import zipfile
from io import BytesIO
import boto3
from boto3.s3.transfer import TransferConfig


class GutenbergDownloader:
    def __init__(
        self,
        bucket_name,
        prefix="gutenberg",
        file_type="txt",
        language="en",
        max_urls=600,
    ):
        self.bucket = bucket_name
        self.prefix = prefix
        self.file_type = file_type
        self.language = language
        self.max_urls = max_urls
        self.base_url = "http://www.gutenberg.org/robot/harvest"
        self.s3 = boto3.client("s3")

        # 10MB multipart upload threshold
        self.config = TransferConfig(multipart_threshold=10 * 1024 * 1024)

        self.headers = {
            "User-Agent": "Mozilla/5.0 (CorpusDownloader/1.0; +https://example.com)"
        }

    def upload_to_s3(self, key, content_bytes):
        self.s3.upload_fileobj(
            BytesIO(content_bytes),
            self.bucket,
            key,
            Config=self.config,
        )
        print(f"Uploaded to s3://{self.bucket}/{key}")

    def get_all_book_urls(self):
        urls = []
        offset = 0

        print(f"Fetching up to {self.max_urls} URLs...")

        while len(urls) < self.max_urls:
            params = {
                "filetypes[]": self.file_type,
                "langs[]": self.language,
                "offset": offset,
            }

            resp = requests.get(self.base_url, params=params,
                                headers=self.headers, timeout=30)
            resp.raise_for_status()

            # Match both absolute and relative URLs
            found = re.findall(
                r'(https?://[^\s"]+\.zip|/[^"\s]+\.zip)', resp.text)

            if not found:
                break

            # Convert relative → absolute
            full_urls = [
                f"https://www.gutenberg.org{u}" if u.startswith("/") else u
                for u in found
            ]

            remaining = self.max_urls - len(urls)
            urls.extend(full_urls[:remaining])

            offset += len(found)
            time.sleep(1)

        return urls

    def download_and_upload_zip(self, url):
        filename = url.split("/")[-1]
        book_id = filename.replace(".zip", "")

        print(f"Downloading {filename}...")

        # Retry logic
        for attempt in range(3):
            try:
                resp = requests.get(url, headers=self.headers, timeout=60)
                resp.raise_for_status()
                break
            except Exception as e:
                print(f"Retry {attempt+1}/3 failed: {e}")
                time.sleep(2)
        else:
            raise RuntimeError(f"Failed to download {url}")

        zip_bytes = resp.content

        # Upload raw ZIP
        self.upload_to_s3(f"{self.prefix}/raw/{filename}", zip_bytes)

        # Extract ZIP in memory
        zip_stream = BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_stream, "r") as z:
            for member in z.namelist():
                extracted = z.read(member)
                s3_key = f"{self.prefix}/extracted/{book_id}/{member}"
                self.upload_to_s3(s3_key, extracted)

    def run(self):
        print("Starting Gutenberg downloader...")

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
        bucket_name="de-27-team4-new",
        prefix="corpus",
        file_type="txt",
        language="en",
        max_urls=600,
    )
    downloader.run()


if __name__ == "__main__":
    main()
