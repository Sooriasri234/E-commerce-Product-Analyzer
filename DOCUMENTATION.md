# Documentation: E-commerce Product Review Analyzer

## Objective

The goal is to help business and product teams understand customer satisfaction from e-commerce review data. The app combines SQL analysis, text classification, feature selection, and visual analytics inside a secure Streamlit dashboard.

## Authentication Design

The landing page displays Login, Register, and Gmail OAuth options together through Streamlit tabs. Local accounts are saved in SQLite with hashed passwords. Sessions use JWT tokens. Gmail OAuth is implemented through Google's OAuth 2.0 authorization flow and can be activated by adding credentials to `.env`.

## Data Pipeline

1. User uploads CSV or Excel data, or the app loads `datasets/sample_reviews.csv`.
2. `preprocessing/text_cleaning.py` detects relevant columns and cleans review text.
3. Ratings are converted into sentiment labels for supervised classification.
4. `model_tuning/tuning.py` trains a TF-IDF plus Logistic Regression pipeline.
5. `model_evaluation/evaluator.py` reports model accuracy, classification metrics, and confusion matrix.
6. `feature_selection/selector.py` identifies the most important sentiment terms.
7. `data_analysis/sql_insights.py` creates SQL-based business summaries.
8. `visualization/charts.py` renders executive-ready Plotly charts.

## SQL Layer

The app loads the cleaned review DataFrame into an in-memory SQLite table named `reviews`. This supports fixed business insights and custom SQL queries from the Streamlit interface.

Example:

```sql
SELECT product_name, category, rating, predicted_sentiment
FROM reviews
ORDER BY rating ASC
LIMIT 10;
```

## Machine Learning

The project uses a classification pipeline:

- Text vectorization: TF-IDF
- Classifier: Logistic Regression
- Tuning: GridSearchCV over TF-IDF feature count and Logistic Regression strength
- Evaluation: accuracy, precision, recall, F1-score, and confusion matrix

For small datasets, the app automatically falls back to a baseline model to avoid unstable cross-validation.

## Deployment Notes

- Keep `.env` out of version control.
- Use a strong `JWT_SECRET` in production.
- Configure Google OAuth redirect URLs for the hosted domain.
- SQLite is suitable for demos and HR submission. For a production multi-user deployment, use PostgreSQL.
