import requests
import polars as pl
import time


def fetch_gutenberg_catalog():
    """Fetch catalog of all Project Gutenberg books"""
    url = "https://gutendex.com/books/"
    all_books = []

    print("Fetching Gutenberg catalog...")
    while url:
        response = requests.get(url)
        data = response.json()

        for book in data["results"]:
            all_books.append(
                {
                    "gutenberg_id": book["id"],
                    "title": book["title"],
                    "authors": (
                        ", ".join([a["name"] for a in book["authors"]])
                        if book["authors"]
                        else "Unknown"
                    ),
                    "languages": ", ".join(book["languages"]),
                    "subjects": (
                        ", ".join(book["subjects"][:3]) if book["subjects"] else ""
                    ),
                    "bookshelves": (
                        ", ".join(book["bookshelves"][:3])
                        if book["bookshelves"]
                        else ""
                    ),
                    "download_count": book["download_count"],
                    "copyright": book["copyright"],
                }
            )

        url = data["next"]  # Pagination
        print(f"Fetched {len(all_books)} books...")
        time.sleep(0.5)

        if len(all_books) >= 1000:  # Get at least 1000 books
            break

    df = pl.DataFrame(all_books)
    df.write_csv("data/gutenberg_full_catalog.csv")
    return df


if __name__ == "__main__":
    df = fetch_gutenberg_catalog()
    print(f"\n✓ Downloaded {len(df)} books")
    print(df.head(10))
