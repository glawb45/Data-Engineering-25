import boto3
import botocore
import json
import csv
import io

REGION = "us-east-1"
BUCKET = "de-27-team4-new"
INPUT_PREFIX = "corpus/extracted/"
OUTPUT_KEY = "corpus/metadata/books_metadata.csv"

MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
MAX_CHARS = 1000


s3 = boto3.client("s3", region_name=REGION)
bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def list_text_files():
    """
    Yield all .txt keys under INPUT_PREFIX in the bucket.
    """
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=INPUT_PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(".txt"):
                yield key


def read_snippet_from_s3(key, max_chars=MAX_CHARS):
    """
    Read the first max_chars characters from a text file in S3.
    """
    resp = s3.get_object(Bucket=BUCKET, Key=key)
    raw = resp["Body"].read(max_chars * 2)  # read a bit more as buffer
    text = raw.decode("utf-8", errors="ignore")
    return text[:max_chars]


def extract_with_bedrock(snippet):
    """
    Ask Claude 3 Haiku to extract structured JSON metadata from the header.
    """
    prompt = f"""
You are a parser for Project Gutenberg book headers.

Given the beginning of a book, extract the following fields if possible:

- title
- author
- release_date
- language
- gutenberg_id (numeric ID if you can find it, otherwise null)

Return ONLY valid JSON with this exact structure:

{{
  "title": "...",
  "author": "...",
  "release_date": "...",
  "language": "...",
  "gutenberg_id": "..."
}}

If you are not sure about a field, set it to null.

Here is the text snippet:
{snippet}
"""

    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 256,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ],
        }
    )

    response = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    response_body = json.loads(response["body"].read())
    reply_text = response_body["content"][0]["text"]

    try:
        md = json.loads(reply_text)
    except json.JSONDecodeError:
        md = {
            "title": None,
            "author": None,
            "release_date": None,
            "language": None,
            "gutenberg_id": None,
        }

    return md


def extract_with_heuristics(snippet):
    """
    Simple non-Bedrock parser using header lines like 'Title:', 'Author:', etc.
    """
    meta = {
        "title": None,
        "author": None,
        "release_date": None,
        "language": None,
        "gutenberg_id": None,
    }

    for line in snippet.splitlines():
        line_stripped = line.strip()
        if ":" not in line_stripped:
            continue

        label, value = line_stripped.split(":", 1)
        label_l = label.strip().lower()
        value = value.strip()

        if not value:
            continue

        if label_l.startswith("title"):
            meta["title"] = meta["title"] or value
        elif label_l.startswith("author"):
            meta["author"] = meta["author"] or value
        elif "release date" in label_l:
            meta["release_date"] = meta["release_date"] or value
        elif label_l.startswith("language"):
            meta["language"] = meta["language"] or value

    return meta


def derive_ids_from_key(key, md):
    """
    Derive book_id and gutenberg_id from the S3 key / metadata.
    Example key: corpus/extracted/10084-8/10084-8.txt
    """
    parts = key.split("/")
    book_id = None
    if len(parts) >= 3:
        book_id = parts[2]  # folder name like 10084-8

    gutenberg_id = md.get("gutenberg_id") or None

    # If Bedrock/heuristic didn't find a numeric ID, try to guess from filename
    if not gutenberg_id:
        filename = parts[-1]  # 10084-8.txt
        base = filename.split(".")[0]
        # strip trailing -x variations if present
        base_numeric = base.split("-")[0]
        if base_numeric.isdigit():
            gutenberg_id = base_numeric

    return book_id, gutenberg_id


def is_complete_case(row):
    """
    Return True if this row has *no* missing key metadata.
    We require title, author, release_date, language, and gutenberg_id.
    """
    required_fields = ["title", "author", "release_date", "language", "gutenberg_id"]
    for f in required_fields:
        val = row.get(f)
        if val is None or str(val).strip() == "":
            return False
    return True


def main():
    rows = []
    use_bedrock = True  # start optimistic

    print(f"Listing text files under s3://{BUCKET}/{INPUT_PREFIX}")
    for i, key in enumerate(list_text_files(), start=1):
        print(f"[{i}] Processing {key}")
        snippet = read_snippet_from_s3(key)

        metadata = None

        if use_bedrock:
            try:
                metadata = extract_with_bedrock(snippet)
            except botocore.exceptions.ClientError as e:
                # Likely AccessDenied or Bedrock not allowed from this role
                print(f"Bedrock error, disabling Bedrock for the rest of the run: {e}")
                use_bedrock = False
            except Exception as e:
                print(f"Unexpected Bedrock error for {key}: {e}")
                use_bedrock = False

        if metadata is None:
            # Either Bedrock was disabled or failed – use heuristics
            metadata = extract_with_heuristics(snippet)

        book_id, gutenberg_id = derive_ids_from_key(key, metadata)

        row = {
            "book_id": book_id,
            "s3_key": key,
            "title": metadata.get("title"),
            "author": metadata.get("author"),
            "release_date": metadata.get("release_date"),
            "language": metadata.get("language"),
            "gutenberg_id": gutenberg_id,
        }

        # *** NEW: only keep complete cases ***
        if is_complete_case(row):
            rows.append(row)
        else:
            print(f"Skipping incomplete metadata for {key}")

    # Write CSV into memory
    fieldnames = [
        "book_id",
        "s3_key",
        "title",
        "author",
        "release_date",
        "language",
        "gutenberg_id",
    ]
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    # Upload CSV to S3
    s3.put_object(
        Bucket=BUCKET,
        Key=OUTPUT_KEY,
        Body=csv_buffer.getvalue().encode("utf-8"),
    )

    print(f"\nDone! Metadata written to s3://{BUCKET}/{OUTPUT_KEY}")
    print(f"Rows kept (complete cases): {len(rows)}")


if __name__ == "__main__":
    main()
