"""Create buckets on the S3-compatible store (LocalStack smoke / MinIO prod).

Usage: S3_ENDPOINT=http://localhost:4566 python infra/s3/init-buckets.py
Creds default to test/test (LocalStack). Prod uses real env vars.
"""
import os
import sys

BUCKETS = ["raw-uploads", "renders", "thumbs", "transcripts"]


def main() -> None:
    try:
        import boto3  # type: ignore
    except ImportError:
        print("boto3 missing: pip install boto3", file=sys.stderr)
        raise SystemExit(2)
    endpoint = os.environ.get("S3_ENDPOINT", "http://localhost:4566")
    s3 = boto3.client(
        "s3", endpoint_url=endpoint,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )
    existing = {b["Name"] for b in s3.list_buckets().get("Buckets", [])}
    for b in BUCKETS:
        if b not in existing:
            s3.create_bucket(Bucket=b)
            print(f"created s3://{b}")
        else:
            print(f"exists s3://{b}")


if __name__ == "__main__":
    main()
