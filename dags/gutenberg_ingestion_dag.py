"""
Airflow DAG for Gutenberg Data Ingestion Pipeline

This DAG orchestrates the complete data ingestion pipeline:
1. Download books from Project Gutenberg to S3
2. Extract metadata using AWS Bedrock
3. Clean and deduplicate metadata

Schedule: Weekly on Sundays at 2 AM UTC
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os

# Add project src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def download_gutenberg_books():
    """Download books from Project Gutenberg to S3"""
    from ingestion.gutenberg_downloader import GutenbergDownloader

    downloader = GutenbergDownloader(
        bucket_name="de-27-team4-new",
        prefix="corpus",
        file_type="txt",
        language="en",
        max_urls=600,
    )
    downloader.run()


def extract_metadata():
    """Extract metadata from downloaded books using AWS Bedrock"""
    from metadata.metadata_extractor import main as extract_main
    extract_main()


def clean_metadata():
    """Clean and deduplicate metadata"""
    from metadata.metadata_cleaner import main as clean_main
    clean_main()


# Default arguments for the DAG
default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=4),
}

# Define the DAG
with DAG(
    'gutenberg_ingestion_pipeline',
    default_args=default_args,
    description='Download and process classic literature from Project Gutenberg',
    schedule_interval='0 2 * * 0',  # Weekly on Sundays at 2 AM UTC
    start_date=datetime(2024, 12, 1),
    catchup=False,
    tags=['gutenberg', 'ingestion', 's3', 'metadata'],
) as dag:

    # Task 1: Download books from Gutenberg
    download_task = PythonOperator(
        task_id='download_gutenberg_books',
        python_callable=download_gutenberg_books,
        execution_timeout=timedelta(hours=3),
    )

    # Task 2: Extract metadata using AWS Bedrock
    extract_task = PythonOperator(
        task_id='extract_metadata',
        python_callable=extract_metadata,
        execution_timeout=timedelta(minutes=45),
    )

    # Task 3: Clean and deduplicate metadata
    clean_task = PythonOperator(
        task_id='clean_metadata',
        python_callable=clean_metadata,
        execution_timeout=timedelta(minutes=10),
    )

    # Task 4: Verify pipeline completion
    verify_task = BashOperator(
        task_id='verify_completion',
        bash_command='echo "Gutenberg ingestion pipeline completed successfully!"',
    )

    # Define task dependencies
    download_task >> extract_task >> clean_task >> verify_task
