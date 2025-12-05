"""
Airflow DAG for Wikipedia Pageviews Streaming Pipeline

This DAG monitors and manages the real-time streaming pipeline:
1. Verify Kafka topic exists
2. Check database connectivity
3. Monitor producer and consumer health
4. Generate health reports

Schedule: Runs every hour
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.python import PythonSensor
import os


def check_kafka_health(**context):
    """Check if Kafka is healthy and topic exists"""
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError

    try:
        bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
        consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            request_timeout_ms=10000,
        )
        topics = consumer.topics()
        consumer.close()

        if 'book_pageviews' in topics:
            print(f"✓ Kafka is healthy. Found topic: book_pageviews")
            return True
        else:
            print(f"✗ Topic 'book_pageviews' not found. Available topics: {topics}")
            return False
    except Exception as e:
        print(f"✗ Kafka health check failed: {e}")
        return False


def check_postgres_health(**context):
    """Check if PostgreSQL is healthy and table exists"""
    from sqlalchemy import create_engine, text

    try:
        database_url = os.getenv('DATABASE_URL',
                                 'postgresql://books_user:books_password@postgres:5432/books_db')
        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Check if book_pageviews table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'book_pageviews'
                );
            """))
            table_exists = result.scalar()

            if table_exists:
                # Get row count
                result = conn.execute(text("SELECT COUNT(*) FROM book_pageviews"))
                count = result.scalar()
                print(f"✓ PostgreSQL is healthy. book_pageviews table has {count} rows")
                return True
            else:
                print("✗ Table 'book_pageviews' does not exist")
                return False
    except Exception as e:
        print(f"✗ PostgreSQL health check failed: {e}")
        return False


def get_streaming_metrics(**context):
    """Collect metrics from the streaming pipeline"""
    from sqlalchemy import create_engine, text

    try:
        database_url = os.getenv('DATABASE_URL',
                                 'postgresql://books_user:books_password@postgres:5432/books_db')
        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Get latest metrics
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT book_id) as unique_books,
                    SUM(pageviews) as total_pageviews,
                    MAX(created_at) as last_update
                FROM book_pageviews
                WHERE created_at > NOW() - INTERVAL '1 hour'
            """))
            row = result.fetchone()

            metrics = {
                'total_records': row[0],
                'unique_books': row[1],
                'total_pageviews': row[2],
                'last_update': str(row[3]) if row[3] else 'N/A'
            }

            print(f"\n📊 Streaming Metrics (Last Hour):")
            print(f"   Total Records: {metrics['total_records']}")
            print(f"   Unique Books: {metrics['unique_books']}")
            print(f"   Total Pageviews: {metrics['total_pageviews']}")
            print(f"   Last Update: {metrics['last_update']}")

            # Push metrics to XCom for downstream tasks
            context['ti'].xcom_push(key='streaming_metrics', value=metrics)

            return metrics
    except Exception as e:
        print(f"✗ Failed to collect metrics: {e}")
        return {}


def alert_if_stale(**context):
    """Alert if no new data has been received in the last hour"""
    from sqlalchemy import create_engine, text
    from datetime import datetime, timedelta

    try:
        database_url = os.getenv('DATABASE_URL',
                                 'postgresql://books_user:books_password@postgres:5432/books_db')
        engine = create_engine(database_url)

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT MAX(created_at) as last_update
                FROM book_pageviews
            """))
            last_update = result.scalar()

            if last_update:
                time_diff = datetime.now() - last_update
                if time_diff > timedelta(hours=1):
                    print(f"⚠️  WARNING: No new data in {time_diff}. Last update: {last_update}")
                    return False
                else:
                    print(f"✓ Data is fresh. Last update: {last_update} ({time_diff} ago)")
                    return True
            else:
                print("⚠️  WARNING: No data found in book_pageviews table")
                return False
    except Exception as e:
        print(f"✗ Staleness check failed: {e}")
        return False


# Default arguments
default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'wikipedia_streaming_monitor',
    default_args=default_args,
    description='Monitor Wikipedia pageviews streaming pipeline health',
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2024, 12, 1),
    catchup=False,
    tags=['streaming', 'kafka', 'wikipedia', 'monitoring'],
) as dag:

    # Task 1: Check PostgreSQL health
    postgres_health_check = PythonOperator(
        task_id='check_postgres_health',
        python_callable=check_postgres_health,
    )

    # Task 2: Collect streaming metrics
    collect_metrics = PythonOperator(
        task_id='collect_streaming_metrics',
        python_callable=get_streaming_metrics,
    )

    # Define task dependencies
    postgres_health_check >> collect_metrics
