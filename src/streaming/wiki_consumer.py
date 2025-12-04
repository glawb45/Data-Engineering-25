import json
from kafka import KafkaConsumer
from datetime import datetime

def run_consumer():
    """Consumes Wikipedia pageview data and prints to console."""
    print("[Consumer] Starting Wikipedia Pageviews Consumer (Console Mode)...\n")
    
    try:
        consumer = KafkaConsumer(
            "book_pageviews",
            bootstrap_servers="localhost:9092",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id="book-pageviews-group",
        )
        print("[Consumer] ✓ Connected to Kafka")
        print("[Consumer] 🎧 Listening for live Wikipedia data...\n")

        count = 0
        for message in consumer:
            try:
                data = message.value
                count += 1
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] #{count} 📚 '{data['book_title']}' by {data['author']}")
                print(f"           └─ {data['pageviews']:,} Wikipedia views")
                print()
                
            except Exception as e:
                print(f"[Consumer ERROR] {e}")
                continue
                
    except Exception as e:
        print(f"[Consumer ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_consumer()
