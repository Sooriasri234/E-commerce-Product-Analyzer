import re
from pathlib import Path
from typing import BinaryIO

import pandas as pd


REVIEW_ALIASES = ["review_text", "review", "reviews", "comment", "comments", "text", "description"]
RATING_ALIASES = ["rating", "ratings", "stars", "score"]
PRODUCT_ALIASES = ["product_name", "product", "item", "title", "sku"]
CATEGORY_ALIASES = ["category", "department", "segment", "product_category"]
DATE_ALIASES = ["review_date", "date", "created_at", "submitted_at"]


def load_dataset(uploaded_file: BinaryIO | None, sample_path: str = "datasets/sample_reviews.csv") -> pd.DataFrame:
    if uploaded_file is None:
        return pd.read_csv(sample_path)

    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    raise ValueError("Upload a CSV, XLSX, or XLS file.")


def _find_column(columns: list[str], aliases: list[str]) -> str | None:
    normalized = {col.lower().strip().replace(" ", "_"): col for col in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    for col in columns:
        key = col.lower().strip()
        if any(alias.replace("_", " ") in key or alias in key for alias in aliases):
            return col
    return None


def clean_text(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.lower()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def sentiment_from_rating(rating: float) -> str:
    if rating >= 4:
        return "Positive"
    if rating <= 2:
        return "Negative"
    return "Neutral"


def normalize_review_dataset(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data.columns = [str(col).strip() for col in data.columns]

    review_col = _find_column(list(data.columns), REVIEW_ALIASES)
    if review_col is None:
        raise ValueError("Could not find a review text column. Use a column like review_text, review, comment, or text.")

    rating_col = _find_column(list(data.columns), RATING_ALIASES)
    product_col = _find_column(list(data.columns), PRODUCT_ALIASES)
    category_col = _find_column(list(data.columns), CATEGORY_ALIASES)
    date_col = _find_column(list(data.columns), DATE_ALIASES)

    normalized = pd.DataFrame()
    normalized["review_text"] = data[review_col].fillna("").astype(str)
    normalized["clean_review"] = normalized["review_text"].map(clean_text)
    normalized["rating"] = pd.to_numeric(data[rating_col], errors="coerce") if rating_col else 3
    normalized["rating"] = normalized["rating"].fillna(3).clip(1, 5)
    normalized["product_name"] = data[product_col].fillna("Unknown Product").astype(str) if product_col else "Unknown Product"
    normalized["category"] = data[category_col].fillna("General").astype(str) if category_col else "General"
    normalized["review_date"] = pd.to_datetime(data[date_col], errors="coerce") if date_col else pd.NaT
    normalized["review_date"] = normalized["review_date"].fillna(pd.Timestamp.today().normalize())
    normalized["review_length"] = normalized["clean_review"].str.split().map(len)
    normalized["rating_sentiment"] = normalized["rating"].map(sentiment_from_rating)
    normalized = normalized[normalized["clean_review"].str.len() > 0].reset_index(drop=True)
    return normalized


def save_processed_dataset(df: pd.DataFrame, output_path: str = "preprocessing/processed_reviews.csv") -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
