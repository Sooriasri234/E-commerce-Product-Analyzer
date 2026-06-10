import json
import os
import re
import sqlite3
from collections import Counter
from io import BytesIO
from textwrap import wrap
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests

from data_analysis.sql_insights import run_query
from preprocessing.text_cleaning import clean_text, normalize_review_dataset


ASPECT_KEYWORDS = {
    "Performance": ["fast", "speed", "slow", "lag", "performance", "powerful", "responsive", "smooth", "crash"],
    "Battery Life": ["battery", "charge", "charging", "lasts", "drain", "power", "hours"],
    "Quality": ["quality", "durable", "broken", "sturdy", "cheap", "premium", "defect", "leaked", "working"],
    "Shipping": ["shipping", "delivery", "arrived", "late", "packaging", "package", "box", "damaged"],
    "Customer Service": ["support", "service", "refund", "replacement", "respond", "helpful", "warranty"],
    "Price": ["price", "value", "expensive", "cheap", "worth", "cost", "deal"],
    "Comfort": ["comfortable", "comfort", "fit", "size", "wear", "soft", "tight"],
    "Design": ["design", "look", "color", "style", "finish", "appearance", "beautiful"],
    "Ease of Use": ["easy", "setup", "install", "clean", "simple", "instructions", "use"],
}

POSITIVE_WORDS = {
    "amazing", "awesome", "best", "bright", "comfortable", "crisp", "durable", "easy", "excellent",
    "fast", "good", "great", "helpful", "love", "perfect", "powerful", "premium", "quick", "smooth",
    "sturdy", "worth",
}
NEGATIVE_WORDS = {
    "bad", "broken", "burning", "cheap", "crash", "damaged", "defect", "drain", "expensive", "hate",
    "late", "leak", "leaked", "lag", "poor", "refund", "slow", "stopped", "terrible", "tight", "worse",
    "worst",
}


def analyze_aspects(df: pd.DataFrame, text_col: str = "clean_review") -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    detail = []
    for idx, row in df.iterrows():
        text = str(row.get(text_col, ""))
        tokens = set(text.split())
        for aspect, keywords in ASPECT_KEYWORDS.items():
            matched = [word for word in keywords if word in tokens or word in text]
            if not matched:
                continue
            pos = sum(1 for word in POSITIVE_WORDS if word in tokens)
            neg = sum(1 for word in NEGATIVE_WORDS if word in tokens)
            if pos > neg:
                sentiment = "Positive"
            elif neg > pos:
                sentiment = "Negative"
            else:
                sentiment = row.get("predicted_sentiment", "Neutral")
            detail.append(
                {
                    "review_index": idx,
                    "product_name": row.get("product_name", "Unknown Product"),
                    "category": row.get("category", "General"),
                    "rating": row.get("rating", 3),
                    "aspect": aspect,
                    "aspect_sentiment": sentiment,
                    "matched_terms": ", ".join(matched[:5]),
                    "review_text": row.get("review_text", ""),
                }
            )

    detail_df = pd.DataFrame(detail)
    if detail_df.empty:
        return pd.DataFrame(columns=["aspect", "mentions", "positive_rate", "negative_rate", "avg_rating"]), detail_df

    summary = (
        detail_df.groupby("aspect", as_index=False)
        .agg(
            mentions=("aspect", "count"),
            positive_rate=("aspect_sentiment", lambda s: round(100 * (s == "Positive").mean(), 1)),
            negative_rate=("aspect_sentiment", lambda s: round(100 * (s == "Negative").mean(), 1)),
            avg_rating=("rating", "mean"),
        )
        .sort_values(["negative_rate", "mentions"], ascending=[False, False])
    )
    summary["avg_rating"] = summary["avg_rating"].round(2)
    return summary, detail_df


def draft_support_response(review: pd.Series, aspect_detail: pd.DataFrame | None = None) -> str:
    product = review.get("product_name", "your product")
    text = str(review.get("review_text", ""))
    rating = review.get("rating", "")
    aspect_text = ""
    if aspect_detail is not None and not aspect_detail.empty:
        aspects = aspect_detail[aspect_detail["review_index"] == review.name]["aspect"].unique().tolist()
        if aspects:
            aspect_text = f" I can see the concern is mainly around {', '.join(aspects[:3]).lower()}."
    issue = text[:220].strip()
    return (
        f"Hi, thank you for taking the time to share this feedback about {product}. "
        f"I'm sorry your experience did not meet expectations, especially with a {rating}-star review.{aspect_text} "
        f"We understand how frustrating this is: \"{issue}\" "
        "Please contact us with your order details so we can review the case, offer troubleshooting, and arrange a replacement, refund, or other resolution where appropriate. "
        "We appreciate the chance to make this right."
    )


def authenticity_scores(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    text = data["clean_review"].fillna("")
    duplicate_counts = text.map(text.value_counts())
    length = data["review_length"].replace(0, np.nan).fillna(1)
    exclamation_count = data["review_text"].fillna("").str.count("!")
    all_caps_words = data["review_text"].fillna("").str.findall(r"\b[A-Z]{4,}\b").map(len)
    mismatch = (
        ((data["rating"] >= 4) & (data["predicted_sentiment"] == "Negative"))
        | ((data["rating"] <= 2) & (data["predicted_sentiment"] == "Positive"))
    ).astype(int)
    same_day_product = data.groupby(["product_name", data["review_date"].dt.date])["review_text"].transform("count")

    score = (
        duplicate_counts.gt(1).astype(int) * 28
        + length.lt(5).astype(int) * 16
        + exclamation_count.gt(3).astype(int) * 10
        + all_caps_words.gt(2).astype(int) * 8
        + mismatch * 24
        + same_day_product.gt(5).astype(int) * 14
    ).clip(0, 100)
    data["authenticity_risk"] = score
    data["authenticity_label"] = pd.cut(
        score,
        bins=[-1, 29, 59, 100],
        labels=["Low risk", "Medium risk", "High risk"],
    ).astype(str)
    data["risk_reasons"] = [
        ", ".join(
            reason
            for reason, active in [
                ("duplicate text", dup > 1),
                ("very short review", words < 5),
                ("rating/sentiment mismatch", bool(mm)),
                ("review burst", burst > 5),
                ("heavy punctuation", bangs > 3),
            ]
            if active
        )
        or "normal pattern"
        for dup, words, mm, burst, bangs in zip(duplicate_counts, length, mismatch, same_day_product, exclamation_count)
    ]
    return data


def build_text_to_sql(question: str) -> str:
    q = question.lower().strip()
    if any(token in q for token in ["drop table", "delete", "insert", "update", "alter", "pragma", "attach"]):
        raise ValueError("Only read-only SELECT questions are supported.")

    month_match = re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b", q)
    month_filter = ""
    if month_match:
        month_num = {
            "january": "01", "february": "02", "march": "03", "april": "04", "may": "05", "june": "06",
            "july": "07", "august": "08", "september": "09", "october": "10", "november": "11", "december": "12",
        }[month_match.group(1)]
        month_filter = f" WHERE strftime('%m', review_date) = '{month_num}'"

    threshold = re.search(r"(?:below|under|less than)\s+(\d+(?:\.\d+)?)", q)
    having = f" HAVING avg_rating < {float(threshold.group(1))}" if threshold else ""

    if "categor" in q and ("average rating" in q or "avg rating" in q or "rating" in q):
        return (
            "SELECT category, COUNT(*) AS review_count, ROUND(AVG(rating), 2) AS avg_rating "
            f"FROM reviews{month_filter} GROUP BY category{having} ORDER BY avg_rating ASC"
        )
    if "negative" in q:
        return (
            "SELECT product_name, category, COUNT(*) AS negative_reviews, ROUND(AVG(rating), 2) AS avg_rating "
            "FROM reviews WHERE predicted_sentiment = 'Negative' "
            "GROUP BY product_name, category ORDER BY negative_reviews DESC, avg_rating ASC LIMIT 20"
        )
    if "product" in q and "rating" in q:
        return (
            "SELECT product_name, category, COUNT(*) AS review_count, ROUND(AVG(rating), 2) AS avg_rating "
            "FROM reviews GROUP BY product_name, category ORDER BY avg_rating ASC LIMIT 20"
        )
    if "sentiment" in q:
        return (
            "SELECT predicted_sentiment, COUNT(*) AS reviews, ROUND(AVG(rating), 2) AS avg_rating "
            "FROM reviews GROUP BY predicted_sentiment ORDER BY reviews DESC"
        )
    return "SELECT product_name, category, rating, predicted_sentiment, review_date, review_text FROM reviews LIMIT 25"


def safe_ai_query(df: pd.DataFrame, question: str) -> tuple[str, pd.DataFrame]:
    sql = build_text_to_sql(question)
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries can be executed.")
    return sql, run_query(df, sql)


def benchmark_brands(datasets: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    normalized_frames = []
    for brand, raw in datasets.items():
        frame = normalize_review_dataset(raw)
        frame["brand"] = brand
        frame["predicted_sentiment"] = frame["rating_sentiment"]
        normalized_frames.append(frame)
    if not normalized_frames:
        return pd.DataFrame(), pd.DataFrame()
    combined = pd.concat(normalized_frames, ignore_index=True)
    aspect_summary, aspect_detail = analyze_aspects(combined)
    brand_summary = (
        combined.groupby("brand", as_index=False)
        .agg(
            reviews=("review_text", "count"),
            avg_rating=("rating", "mean"),
            positive_rate=("predicted_sentiment", lambda s: round(100 * (s == "Positive").mean(), 1)),
            negative_rate=("predicted_sentiment", lambda s: round(100 * (s == "Negative").mean(), 1)),
        )
        .sort_values("avg_rating", ascending=False)
    )
    brand_summary["avg_rating"] = brand_summary["avg_rating"].round(2)
    if aspect_detail.empty:
        return brand_summary, pd.DataFrame()
    aspect_brand = (
        aspect_detail.assign(brand=combined.loc[aspect_detail["review_index"], "brand"].values)
        .groupby(["brand", "aspect"], as_index=False)
        .agg(mentions=("aspect", "count"), negative_rate=("aspect_sentiment", lambda s: round(100 * (s == "Negative").mean(), 1)))
        .sort_values(["aspect", "negative_rate"], ascending=[True, False])
    )
    return brand_summary, aspect_brand


def generate_report_pdf(analyzed: pd.DataFrame, insights: pd.DataFrame, aspect_summary: pd.DataFrame) -> bytes:
    lines = [
        "E-commerce Product Review Analyzer Report",
        "",
        f"Reviews analyzed: {len(analyzed):,}",
        f"Average rating: {analyzed['rating'].mean():.2f} / 5",
        f"Positive sentiment: {(analyzed['predicted_sentiment'] == 'Positive').mean() * 100:.1f}%",
        f"Negative sentiment: {(analyzed['predicted_sentiment'] == 'Negative').mean() * 100:.1f}%",
        "",
        "Top SQL Insight Rows",
    ]
    for _, row in insights.head(8).iterrows():
        lines.append(" | ".join(f"{col}: {row[col]}" for col in insights.columns[:5]))
    lines.extend(["", "Aspect Summary"])
    for _, row in aspect_summary.head(8).iterrows():
        lines.append(
            f"{row['aspect']}: {row['mentions']} mentions, {row['positive_rate']}% positive, {row['negative_rate']}% negative"
        )
    return _simple_pdf(lines)


def _simple_pdf(lines: list[str]) -> bytes:
    stream_lines = ["BT", "/F1 14 Tf", "50 790 Td", "18 TL"]
    first = True
    for line in lines:
        for part in wrap(str(line), width=88) or [""]:
            escaped = part.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            if first:
                stream_lines.append(f"({escaped}) Tj")
                first = False
            else:
                stream_lines.append(f"T* ({escaped}) Tj")
    stream_lines.append("ET")
    content = "\n".join(stream_lines).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    pdf = BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(pdf.tell())
        pdf.write(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = pdf.tell()
    pdf.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.write(f"{offset:010d} 00000 n \n".encode())
    pdf.write(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return pdf.getvalue()


def scrape_reviews_from_url(url: str) -> pd.DataFrame:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Enter a valid http or https product URL.")
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ReviewAnalyzer/1.0)",
        "Accept-Language": "en-US,en;q=0.9",
    }
    response = requests.get(url, headers=headers, timeout=12)
    response.raise_for_status()
    html = response.text
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    product_name = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else parsed.netloc

    candidates = []
    for pattern in [
        r'"reviewBody"\s*:\s*"([^"]{20,1000})"',
        r'"reviewText"\s*:\s*"([^"]{20,1000})"',
        r'<p[^>]*class="[^"]*review[^"]*"[^>]*>(.*?)</p>',
        r'<span[^>]*class="[^"]*review[^"]*"[^>]*>(.*?)</span>',
    ]:
        candidates.extend(re.findall(pattern, html, re.I | re.S))

    cleaned = []
    for item in candidates:
        text = re.sub(r"<[^>]+>", " ", item)
        text = re.sub(r"\\n|\\r|&quot;|&#34;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) >= 20:
            cleaned.append(text)
    unique_reviews = list(dict.fromkeys(cleaned))[:100]
    if not unique_reviews:
        raise ValueError("No reviews were detected on this page. Some marketplaces block scraping or load reviews dynamically.")
    return pd.DataFrame(
        {
            "product_name": product_name[:120],
            "category": parsed.netloc,
            "rating": 3,
            "review_text": unique_reviews,
            "review_date": pd.Timestamp.today().normalize(),
        }
    )
