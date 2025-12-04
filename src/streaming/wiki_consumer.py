import json
import os
from datetime import datetime
from kafka import KafkaConsumer
from sqlalchemy import create_engine, text

# Kafka config
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "book_pageviews")

# Database config
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://books_user:books_password@localhost:5432/books_db"
)

# Create DB engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def insert_into_db(data):
    """Insert a Kafka message into the book_pageviews table."""
    insert_query = text(
        """
        INSERT INTO book_pageviews (
            book_id,
            book_title,
            author,
            pageviews,
            timestamp,
            data_timestamp
        )
        VALUES (
            :book_id,
            :book_title,
            :author,
            :pageviews,
            :timestamp,
            :data_timestamp
        )
    """
    )

    try:
        with engine.begin() as conn:
            conn.execute(insert_query, data)
        print(f"[DB] Inserted row for {data['book_title']} ({data['pageviews']} views)")
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return


def run_consumer():
    """Consumes Wikipedia pageview data and writes to PostgreSQL."""
    print("[Consumer] Starting Wikipedia Pageviews Consumer...")

    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id="book-pageviews-group",
        )
        print("[Consumer] ✓ Connected to Kafka")
        print("[Consumer] 🎧 Listening for live book traffic...\n")

        for message in consumer:
            data = message.value

            # Convert timestamp from string → datetime
            try:
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            except:
                data["timestamp"] = datetime.now()

            print(f"[Kafka] {data['book_title']} → {data['pageviews']} views")

            # Insert into DB
            insert_into_db(data)

    except Exception as e:
        print(f"[Consumer ERROR] {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_consumer()
