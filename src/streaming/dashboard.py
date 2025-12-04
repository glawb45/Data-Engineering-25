import os
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Live Book Interest Dashboard", layout="wide")
st.title("📚 Live Classic Literature Interest Dashboard")
st.markdown(
    "**Real-time Wikipedia pageview data showing current interest in classic books**"
)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://books_user:books_password@localhost:5432/books_db"
)


@st.cache_resource
def get_engine(url: str):
    return create_engine(url, pool_pre_ping=True)


engine = get_engine(DATABASE_URL)


def load_data(limit: int = 500) -> pd.DataFrame:
    query = """
        SELECT * FROM book_pageviews 
        ORDER BY timestamp DESC 
        LIMIT :limit
    """
    try:
        df = pd.read_sql_query(
            text(query), con=engine.connect(), params={"limit": limit}
        )
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def get_latest_by_book() -> pd.DataFrame:
    """Get the most recent pageview count for each book."""
    query = """
        SELECT DISTINCT ON (book_id) 
            book_id, book_title, author, pageviews, timestamp
        FROM book_pageviews
        ORDER BY book_id, timestamp DESC
    """
    try:
        df = pd.read_sql_query(text(query), con=engine.connect())
        return df
    except:
        return pd.DataFrame()


# Sidebar
update_interval = st.sidebar.slider("Update Interval (seconds)", 3, 30, 10)
limit_records = st.sidebar.number_input("Records to load", 100, 2000, 500, 100)

if st.sidebar.button("Refresh Now"):
    st.rerun()

placeholder = st.empty()

while True:
    df_all = load_data(limit=int(limit_records))
    df_latest = get_latest_by_book()

    with placeholder.container():
        if df_all.empty:
            st.warning("Waiting for data from Kafka stream...")
            time.sleep(update_interval)
            continue

        df_all["timestamp"] = pd.to_datetime(df_all["timestamp"])

        # KPIs
        total_records = len(df_all)
        total_views = df_all["pageviews"].sum()
        unique_books = df_all["book_id"].nunique()
        avg_views = df_all["pageviews"].mean()

        st.subheader(f"📊 Live Statistics")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Data Points", f"{total_records:,}")
        k2.metric("Total Pageviews Tracked", f"{total_views:,}")
        k3.metric("Books Monitored", unique_books)
        k4.metric("Avg Views per Update", f"{avg_views:,.0f}")

        # Current interest
        if not df_latest.empty:
            st.subheader("📖 Current Interest (Latest Data)")
            fig_current = px.bar(
                df_latest.sort_values("pageviews", ascending=True),
                y="book_title",
                x="pageviews",
                orientation="h",
                title="Wikipedia Pageviews - Last Hour",
                labels={"pageviews": "Views", "book_title": "Book"},
                color="pageviews",
                color_continuous_scale="Blues",
            )
            st.plotly_chart(fig_current, use_container_width=True)

        # Time series
        st.subheader("📈 Interest Over Time")
        fig_timeline = px.line(
            df_all,
            x="timestamp",
            y="pageviews",
            color="book_title",
            title="Pageviews Timeline (Live Stream)",
            labels={"timestamp": "Time", "pageviews": "Wikipedia Views"},
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

        # Recent data table
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔍 Most Recent Updates")
            st.dataframe(
                df_all[["book_title", "author", "pageviews", "timestamp"]].head(10),
                use_container_width=True,
            )

        with col2:
            st.subheader("📚 By Author")
            author_stats = (
                df_all.groupby("author")["pageviews"].agg(["sum", "mean"]).reset_index()
            )
            author_stats.columns = ["Author", "Total Views", "Avg Views"]
            st.dataframe(author_stats, use_container_width=True)

        st.markdown("---")
        st.caption(
            f"🟢 Live data from Wikipedia API | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: {update_interval}s"
        )

    time.sleep(update_interval)
