import time
import json
import requests
from datetime import datetime, timedelta
from kafka import KafkaProducer
import pandas as pd

def get_wikipedia_title(book_title, author):
    """Convert book title to Wikipedia article format."""
    # Most books follow this pattern: "Title (Author book)" or just "Title"
    # We'll try the simple title first
    clean_title = book_title.strip().replace(' ', '_')
    return clean_title

def fetch_wikipedia_pageviews(article_title):
    """
    Fetches real-time Wikipedia pageview data for the last hour.
    API: https://wikimedia.org/api/rest_v1/
    """
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    today = datetime.now().strftime('%Y%m%d')
    
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{article_title}/daily/{yesterday}/{today}"
    
    try:
        response = requests.get(url, headers={'User-Agent': 'BookDashboard/1.0'})
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                latest = data['items'][-1]
                return {
                    'views': latest['views'],
                    'timestamp': latest['timestamp']
                }
    except Exception as e:
        print(f"Error fetching data for {article_title}: {e}")
    
    return {'views': 0, 'timestamp': datetime.now().strftime('%Y%m%d%H')}

def load_books_metadata(csv_path='../../data/books_metadata_clean.csv'):
    """Load books from your CSV file."""
    df = pd.read_csv(csv_path)
    return df

def run_producer():
    """Kafka producer that sends live Wikipedia pageview data."""
    print("[Producer] Starting Wikipedia Pageviews Producer...")
    print("[Producer] This fetches REAL live data about how many people")
    print("[Producer] are viewing Wikipedia pages for classic books RIGHT NOW!\n")
    
    try:
        producer = KafkaProducer(
            bootstrap_servers="localhost:9092",
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=30000,
        )
        print("[Producer] ✓ Connected to Kafka\n")
        
        # Load your books
        books_df = load_books_metadata()
        print(f"[Producer] Loaded {len(books_df)} books from metadata\n")
        
        # Focus on popular books (you can adjust this list)
        featured_books = [
            ("A Christmas Carol", "Charles Dickens"),
            ("Alice Adams", "Booth Tarkington"),
            ("Pride and Prejudice", "Jane Austen"),  # if in your data
        ]
        
        count = 0
        while True:
            # Rotate through books
            for book_title, author in featured_books:
                wiki_title = get_wikipedia_title(book_title, author)
                
                print(f"[Producer] Fetching live data for '{book_title}' by {author}...")
                pageview_data = fetch_wikipedia_pageviews(wiki_title)
                
                message = {
                    'book_id': f"{book_title}_{author}".replace(' ', '_'),
                    'book_title': book_title,
                    'author': author,
                    'wikipedia_title': wiki_title,
                    'pageviews': pageview_data['views'],
                    'timestamp': datetime.now().isoformat(),
                    'data_timestamp': pageview_data['timestamp']
                }
                
                print(f"[Producer] 📊 {book_title}: {pageview_data['views']} views")
                producer.send("book_pageviews", value=message)
                producer.flush()
                
                count += 1
                time.sleep(2)  # Small delay between books
            
            print(f"\n[Producer] ✓ Cycle complete. Waiting 60 seconds for fresh data...\n")
            time.sleep(60)  # Wikipedia data updates hourly, so check every minute
            
    except Exception as e:
        print(f"[Producer ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_producer()

