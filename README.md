# E-commerce Product Review Analyzer

A professional Streamlit project for analyzing e-commerce product reviews with authentication, Gmail OAuth, SQL insights, text classification, feature selection, model evaluation, model tuning, aspect-based sentiment analysis, review authenticity scoring, competitor benchmarking, automated reports, and interactive customer satisfaction dashboards.

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
- Plain-English SQL assistant that converts common business questions into safe read-only SQL queries.
- Sentiment classification with TF-IDF and Logistic Regression.
- Model tuning with GridSearchCV when enough data is available.
- Single-class fallback model for small or one-sentiment datasets so imports do not crash the analyzer.
- Model evaluation with accuracy, classification report, and confusion matrix.
- Feature selection using TF-IDF and chi-square term scoring.
- Aspect-Based Sentiment Analysis (ABSA) for product aspects such as performance, battery life, quality, shipping, customer service, price, comfort, design, and ease of use.
- Automated customer support response drafts for negative reviews, with product-specific and issue-aware wording.
- Review Authenticity / Fake Review Detector that flags duplicate text, very short reviews, rating/sentiment mismatches, heavy punctuation, and review bursts.
- Competitor Benchmarking for comparing multiple uploaded brand datasets side-by-side by rating, sentiment, and aspect weakness.
- Automated PDF reporting that summarizes the current dashboard, sentiment mix, SQL insights, and ABSA results.
- Email draft shortcut for sharing weekly stakeholder reports.
- Live review import from product URLs, including Amazon, Shopify, eBay, or generic product pages when reviews are available in the page HTML.
- Feedback Theme Analysis using extracts and clusters common topics from positive and negative reviews using TF-IDF + KMeans clustering to identify key customer pain points and strengths.
- Actionable Recommendations that generates business recommendations based on feedback themes, categorized as Reinforce (positive feedback), Address (negative feedback), and Health Check (overall sentiment health).
- Keyword Insights used to identify the most frequent and important keywords per sentiment for quick actionable insights.
- Interactive Plotly dashboards for sentiment mix, category satisfaction, and rating trends.
- Compact e-commerce mode selector with Default, Light, and Dark options.
- Dark-mode file uploader styling fix so the Browse files button remains visible.
- Processed review export as CSV.
- Analysis history stored per authenticated user.

## Dashboard Tabs

After login and data loading, the analyzer shows these dashboard tabs:

- **Overview**: Displays sentiment mix, category satisfaction, and rating trend charts using interactive Plotly visualizations.
- **SQL Insights**: Shows customer satisfaction summaries, product risk tables, keyword behavior, raw SQL execution, and a plain-English AI data assistant for common analytics questions.
- **ABSA**: Shows aspect-level sentiment summaries and lets you inspect review examples for each product aspect.
- **Support Drafts**: Lets sellers select a negative review and generate a personalized response draft.
- **Authenticity**: Scores reviews for possible fake, incentivized, bot-like, or anomalous patterns.
- **Benchmarking**: Accepts multiple competitor or brand datasets and compares performance side-by-side.
- **Reports**: Generates a downloadable PDF report and opens an email draft for stakeholder sharing.
- **Classification**: Displays the sentiment classification model details, tuning mode, accuracy, classification report, and confusion matrix.
- **Feature Selection**: Lists important TF-IDF and chi-square terms that help distinguish sentiment classes.
- **Customer Feedback**: Extracts customer feedback themes, action items, positive feedback, negative issues, neutral feedback, and top keywords by sentiment.
- **Data Preview**: Shows the processed review dataset and provides a CSV download for analyzed reviews.

## Live URL Import

The dashboard includes a **Live review import from product URL** expander above the main analyzer. Paste a product URL and click **Fetch live reviews** to attempt importing reviews directly into the analyzer.

Some marketplaces load reviews dynamically or block scraping, so URL import is best-effort. CSV and Excel upload remains the most reliable workflow.

## Plain-English SQL Examples

```text
Show me all categories where the average rating dropped below 3 in March
Show negative products
Show sentiment summary
Show products by rating
```

The assistant only executes generated `SELECT` queries and blocks write-style SQL keywords such as `DELETE`, `UPDATE`, `INSERT`, `ALTER`, and `DROP`.

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
advanced_features.py
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
