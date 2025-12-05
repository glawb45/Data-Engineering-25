import polars as pl
import numpy as np
from sklearn.linear_model import LinearRegression

df = pl.read_csv("data/gutenberg_full_catalog.csv")

print("Rows:", df.height, "Columns:", df.width)
print(df.head())

# Basic cleaning / feature engineering
df = df.with_columns([
    pl.col("download_count").cast(pl.Int64),
    pl.col("title").str.len_chars().alias("title_length"),
    pl.col("subjects").str.len_chars().alias("subjects_length"),
    (pl.col("copyright") == False).cast(pl.Int8).alias("is_public_domain"),
])

# Descriptive statistics
print("\n=== Download count summary ===")
print(df["download_count"].describe())

print("\nTop 10 most downloaded books:")
print(
    df.select(["title", "authors", "download_count"])
      .sort("download_count", descending=True)
      .head(10)
)

print("\nDownloads by language (top 10):")
print(
    df.group_by("languages")
      .agg(pl.col("download_count").sum().alias("total_downloads"))
      .sort("total_downloads", descending=True)
      .head(10)
)

# Simple regression: do longer titles get more downloads?

# Regression: download_count ~ language (top 5 languages one‑hot encoded)

# Find top 5 languages by total downloads
lang_stats = (
    df.group_by("languages")
      .agg(pl.col("download_count").sum().alias("total_downloads"))
      .sort("total_downloads", descending=True)
)
top_langs = lang_stats["languages"][:5].to_list()
print("\nTop 5 languages by total downloads:", top_langs)

# Create one‑hot columns for top 5 languages
df_lang = df.with_columns([
    *(pl.when(pl.col("languages") == lang)
        .then(1)
        .otherwise(0)
        .alias(f"is_{lang}")
      for lang in top_langs)
])

# Keep only rows with non-null download_count
df_reg = df_lang.drop_nulls(["download_count"])

feature_cols = [f"is_{lang}" for lang in top_langs]
X = df_reg.select(feature_cols).to_numpy()
y = df_reg["download_count"].to_numpy()

model = LinearRegression()
model.fit(X, y)

r2 = model.score(X, y)
coefs = model.coef_
intercept = model.intercept_

print("\n=== Regression: download_count ~ language (top 5 one‑hot) ===")
print(f"Number of books: {len(df_reg)}")
print("Features:", feature_cols)
print("Coefficients:", [f"{c:.1f}" for c in coefs])
print(f"Intercept: {intercept:.1f}")
print(f"R²: {r2:.4f}")

