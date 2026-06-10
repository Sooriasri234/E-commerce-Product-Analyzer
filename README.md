# E-commerce Product Review Analyzer

A professional Streamlit project for analyzing e-commerce product reviews with authentication, Gmail OAuth, SQL insights, text classification, feature selection, model evaluation, model tuning, and interactive customer satisfaction dashboards.

## Project Category

This project comes under **Classification**.

The model classifies each product review into sentiment classes: **Positive**, **Neutral**, or **Negative**. The target label is derived from customer ratings:

- 4-5 stars: Positive
- 3 stars: Neutral
- 1-2 stars: Negative

It is not primarily regression because the output is not a continuous numeric value. It is not clustering because labels are known or derived. It is not forecasting because it does not predict future time periods.

## Core Features

- Single-page authentication with Login, Register, and Gmail OAuth tabs.
- Secure password hashing with `passlib`.
- JWT-backed session handling.
- Optional Google OAuth using Gmail credentials.
- Upload your own CSV, XLSX, or XLS review dataset.
- Automatic column detection for review text, ratings, product names, categories, and review dates.
- SQL analytics over the cleaned review table using SQLite.
- Sentiment classification with TF-IDF and Logistic Regression.
- Model tuning with GridSearchCV when enough data is available.
- Model evaluation with accuracy, classification report, and confusion matrix.
- Feature selection using TF-IDF and chi-square term scoring.
- Feedback Theme Analysis using extracts and clusters common topics from positive and negative reviews using TF-IDF + KMeans clustering to identify key customer pain points and strengths.
- Actionable Recommendations that generates business recommendations based on feedback themes, categorized as Reinforce (positive feedback), Address (negative feedback), and Health Check (overall sentiment health).
- Keyword Insights used to identify the most frequent and important keywords per sentiment for quick actionable insights.
- Interactive Plotly dashboards for sentiment mix, category satisfaction, and rating trends.
- Compact e-commerce mode selector with Default, Light, and Dark options.
- Processed review export as CSV.
- Analysis history stored per authenticated user.


## Folder Structure

```text
datasets/
  sample_reviews.csv
data_analysis/
  sql_insights.py
preprocessing/
  text_cleaning.py
visualization/
  charts.py
feature_selection/
  selector.py
model_evaluation/
  evaluator.py
model_tuning/
  tuning.py
deployment/
  app_config.py
  review_analyzer.db
app.py
auth.py
database.py
feedback_analyzer.py
google_oauth.py
styles.py
requirements.txt
preview.txt
DOCUMENTATION.md
```

## Dataset Format

Minimum required column:

- `review_text`, `review`, `comment`, `comments`, `text`, or `description`

Recommended columns:

- `rating`
- `product_name`
- `category`
- `review_date`

If optional columns are missing, the app fills professional defaults so the analyzer still works.

## Setup

```bash
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

On Linux or macOS, use `cp .env.example .env`.

## Google OAuth Setup

1. Open Google Cloud Console.
2. Create OAuth 2.0 credentials for a web application.
3. Add your Streamlit URL as an authorized redirect URI.
4. Set these values in `.env`:

```bash
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8501
```

For deployment, replace the redirect URI with your hosted Streamlit app URL.

## Run

```bash
streamlit run app.py
```

After login, upload a review file or use the included sample dataset. All analyzer features become visible after successful authentication.

## Share a Link

`http://localhost:8501` works only on the computer running the app. To send a link to a friend, deploy the project on Streamlit Community Cloud:

1. Push this project to a GitHub repository.
2. Open Streamlit Community Cloud.
3. Create a new app from the repository.
4. Set the main file path as `app.py`.
5. Add Google OAuth values in the app secrets if Gmail login is required.
