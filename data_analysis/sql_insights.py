import sqlite3

import pandas as pd


def create_review_connection(df: pd.DataFrame) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    df.to_sql("reviews", conn, index=False, if_exists="replace")
    return conn


def run_query(df: pd.DataFrame, sql: str) -> pd.DataFrame:
    with create_review_connection(df) as conn:
        return pd.read_sql_query(sql, conn)


def satisfaction_summary(df: pd.DataFrame) -> pd.DataFrame:
    return run_query(
        df,
        """
        SELECT
            category,
            COUNT(*) AS review_count,
            ROUND(AVG(rating), 2) AS avg_rating,
            ROUND(100.0 * SUM(CASE WHEN predicted_sentiment = 'Positive' THEN 1 ELSE 0 END) / COUNT(*), 2) AS positive_rate,
            ROUND(100.0 * SUM(CASE WHEN predicted_sentiment = 'Negative' THEN 1 ELSE 0 END) / COUNT(*), 2) AS negative_rate
        FROM reviews
        GROUP BY category
        ORDER BY review_count DESC, avg_rating DESC
        """,
    )


def product_risk_table(df: pd.DataFrame) -> pd.DataFrame:
    return run_query(
        df,
        """
        SELECT
            product_name,
            category,
            COUNT(*) AS review_count,
            ROUND(AVG(rating), 2) AS avg_rating,
            SUM(CASE WHEN predicted_sentiment = 'Negative' THEN 1 ELSE 0 END) AS negative_reviews
        FROM reviews
        GROUP BY product_name, category
        HAVING review_count >= 1
        ORDER BY negative_reviews DESC, avg_rating ASC
        LIMIT 10
        """,
    )


def keyword_signal_table(df: pd.DataFrame) -> pd.DataFrame:
    return run_query(
        df,
        """
        SELECT
            predicted_sentiment,
            COUNT(*) AS reviews,
            ROUND(AVG(review_length), 1) AS avg_review_length,
            ROUND(AVG(rating), 2) AS avg_rating
        FROM reviews
        GROUP BY predicted_sentiment
        ORDER BY reviews DESC
        """,
    )
