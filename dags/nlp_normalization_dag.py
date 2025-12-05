"""
Airflow DAG for Text Normalization Pipeline

This DAG handles the training and application of the spelling normalization model:
1. Train the Bayesian normalizer on Shakespeare corpus
2. Normalize texts for downstream analysis
3. Evaluate model accuracy

Schedule: Weekly on Saturdays at 3 AM UTC
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os

# Add project src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def train_normalizer(**context):
    """Train the spelling normalizer on Shakespeare corpus"""
    import sys

    # Set up command-line arguments for train_and_test.py
    sys.argv = [
        'train_and_test.py',
        '--input', '/opt/airflow/data/FullShakespeare.txt',
        '--split', '0.8',
        '--seed', '42'
    ]

    print("Training spelling normalizer...")
    try:
        from train_and_test import main as train_main
        train_main()
        print("✓ Normalizer training completed successfully")
        return True
    except Exception as e:
        print(f"✗ Training failed: {e}")
        raise


def test_normalizer(**context):
    """Test the trained normalizer with sample texts"""
    from normalize_spelling import build_normalizer

    normalizer = build_normalizer()

    # Sample texts to normalize
    samples = [
        "Thou art a noble knight, methinks.",
        "'Tis but a scratch!",
        "Whither goest thou?",
    ]

    print("\n📝 Sample Normalizations:")
    for original in samples:
        normalized = normalizer(original)
        print(f"   Original:   {original}")
        print(f"   Normalized: {normalized}")
        print()

    print("✓ Normalizer test completed successfully")
    return True


# Default arguments
default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'nlp_normalization_pipeline',
    default_args=default_args,
    description='Train and apply spelling normalization for Early Modern English',
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2024, 12, 1),
    catchup=False,
    tags=['nlp', 'normalization', 'shakespeare', 'training'],
) as dag:

    # Task 1: Train the normalizer
    train_task = PythonOperator(
        task_id='train_normalizer',
        python_callable=train_normalizer,
        execution_timeout=timedelta(minutes=30),
    )

    # Task 2: Test with sample texts
    test_task = PythonOperator(
        task_id='test_normalizer',
        python_callable=test_normalizer,
        execution_timeout=timedelta(minutes=5),
    )

    # Define task dependencies
    train_task >> test_task
