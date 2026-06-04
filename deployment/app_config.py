from pathlib import Path


APP_NAME = "E-commerce Product Review Analyzer"
PROJECT_CATEGORY = "Classification"
DB_PATH = Path("deployment/review_analyzer.db")
SAMPLE_DATASET_PATH = Path("datasets/sample_reviews.csv")

REQUIRED_REVIEW_COLUMNS = {
    "minimum": "A text column such as review_text, review, comment, or text.",
    "recommended": "rating, product_name, category, review_date.",
}
