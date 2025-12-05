import re
import io

import boto3
import pandas as pd

REGION = "us-east-1"
BUCKET = "de-27-team4-new"
INPUT_KEY = "corpus/metadata/books_metadata.csv"
OUTPUT_KEY = "corpus/metadata/books_metadata_clean.csv"


s3 = boto3.client("s3", region_name=REGION)


def clean_release_date(value):
    """
    Remove trailing [EBook #xxxx], [Etext #xxxx], etc. from the release_date.
    """
    if pd.isna(value):
        return value
    text = str(value)
    # Remove any " [ ... ]" chunk at the end
    text = re.sub(r"\s*\[[^\]]*\]\s*$", "", text)
    return text.strip()


def main():
    # 1. Read original CSV from S3
    print(f"Reading s3://{BUCKET}/{INPUT_KEY}")
    resp = s3.get_object(Bucket=BUCKET, Key=INPUT_KEY)
    body = resp["Body"].read()
    df = pd.read_csv(io.BytesIO(body))

    print(f"Original row count: {len(df)}")

    # 2. Clean release_date
    df["release_date"] = df["release_date"].apply(clean_release_date)

    # 3. Drop rows where book_id ends with '-8'
    mask_minus8 = df["book_id"].astype(str).str.endswith("-8")
    num_minus8 = mask_minus8.sum()
    print(f"Removing {num_minus8} rows where book_id ends with '-8'")
    df = df[~mask_minus8].copy()

    # 4. Drop redundant columns (gutenberg_id, language) because gutenberg_id is the same as book_id and all are in english
    cols_to_drop = []
    if "gutenberg_id" in df.columns:
        cols_to_drop.append("gutenberg_id")
    if "language" in df.columns:
        cols_to_drop.append("language")

    print(f"Dropping columns: {cols_to_drop}")
    df = df.drop(columns=cols_to_drop)

    # 5. Cleaned CSV back to S3
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    s3.put_object(Bucket=BUCKET, Key=OUTPUT_KEY, Body=csv_bytes)

    print(f"Saved cleaned data to s3://{BUCKET}/{OUTPUT_KEY}")
    print(f"Final row count: {len(df)}")


if __name__ == "__main__":
    main()
