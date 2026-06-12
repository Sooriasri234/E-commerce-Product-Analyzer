from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from advanced_features import (
    analyze_aspects,
    authenticity_scores,
    benchmark_brands,
    draft_support_response,
    generate_report_pdf,
    safe_ai_query,
    scrape_reviews_from_url,
)
from auth import authenticate_user, create_access_token, decode_access_token, register_user
from data_analysis.sql_insights import keyword_signal_table, product_risk_table, satisfaction_summary
from database import get_recent_runs, init_db, record_analysis_run
from deployment.app_config import APP_NAME, REQUIRED_REVIEW_COLUMNS
from feature_selection.selector import top_discriminative_terms
from feedback_analyzer import extract_feedback_themes, generate_recommendations, get_top_keywords_by_sentiment
from google_oauth import complete_google_login, get_google_login_url, is_google_oauth_configured
from model_evaluation.evaluator import evaluate_model
from model_tuning.tuning import train_tuned_classifier
from preprocessing.text_cleaning import load_dataset, normalize_review_dataset, save_processed_dataset
from styles import apply_theme
from visualization.charts import category_satisfaction_bar, confusion_heatmap, sentiment_donut, trend_line


st.set_page_config(page_title=APP_NAME, page_icon="cart", layout="wide", initial_sidebar_state="expanded")


def initialize_state() -> None:
    init_db()
    st.session_state.setdefault("jwt", None)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("last_recorded_signature", None)
    st.session_state.setdefault("theme_mode", "Default")
    st.session_state.setdefault("live_review_df", None)
    st.session_state.setdefault("live_review_source", None)


def hydrate_user_from_token() -> None:
    if st.session_state.user or not st.session_state.jwt:
        return
    payload = decode_access_token(st.session_state.jwt)
    if payload:
        st.session_state.user = {
            "id": payload["sub"],
            "name": payload.get("name", "User"),
            "email": payload.get("email", ""),
            "provider": payload.get("provider", "local"),
        }


def set_logged_in(user: dict) -> None:
    st.session_state.jwt = create_access_token(user)
    st.session_state.user = user
    st.query_params.clear()
    st.rerun()


def theme_switcher(location: str) -> None:
    _, default_col, light_col, dark_col = st.columns([1, 0.055, 0.055, 0.055])
    with default_col:
        if st.button("⚙", key=f"default_theme_{location}", help="Default mode"):
            st.session_state.theme_mode = "Default"
            st.rerun()
    with light_col:
        if st.button("☀", key=f"light_theme_{location}", help="Light mode"):
            st.session_state.theme_mode = "Light"
            st.rerun()
    with dark_col:
        if st.button("☾", key=f"dark_theme_{location}", help="Dark mode"):
            st.session_state.theme_mode = "Dark"
            st.rerun()
    st.markdown(f'<div class="theme-status">{st.session_state.theme_mode} mode</div>', unsafe_allow_html=True)


def auth_page() -> None:
    google_user = complete_google_login()
    if google_user:
        set_logged_in(google_user)

    apply_theme(st.session_state.theme_mode)
    theme_switcher("auth")

    st.markdown(
        """
        <div class="auth-shell">
            <div class="auth-header">
                <h1>E-commerce Product Review Analyzer</h1>
                <p>Securely sign in to classify review sentiment, query insights with SQL, and visualize product satisfaction metrics.</p>
                <div class="google-badge"><span class="google-mark">G</span><span>Gmail OAuth supported on this page</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, register_tab, gmail_tab = st.tabs(["Login", "Register", "Continue with Gmail"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="analyst@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            user = authenticate_user(email, password)
            if user:
                set_logged_in(user)
            else:
                st.error("Invalid email or password.")

    with register_tab:
        with st.form("register_form"):
            name = st.text_input("Full name")
            reg_email = st.text_input("Work email")
            reg_password = st.text_input("Create password", type="password", placeholder="4 to 7 characters")
            created = st.form_submit_button("Create account", use_container_width=True)
        if created:
            try:
                set_logged_in(register_user(name, reg_email, reg_password))
            except ValueError as exc:
                st.error(str(exc))

    with gmail_tab:
        st.markdown('<div class="google-badge"><span class="google-mark">G</span><span>Sign in with your Gmail account</span></div>', unsafe_allow_html=True)
        if is_google_oauth_configured():
            login_url = get_google_login_url()
            st.markdown(
                f'''<a class="google-auth-link" href="{login_url}" target="_blank" rel="noreferrer">
                    <span class="google-auth-icon">G</span>
                    Continue with Google
                </a>''',
                unsafe_allow_html=True,
            )
        else:
            st.info("Google OAuth is ready in the code. Add Google client settings in `.env` to activate the Gmail login button.")
            st.code(
                "GOOGLE_CLIENT_ID=your-client-id\nGOOGLE_CLIENT_SECRET=your-client-secret\nGOOGLE_REDIRECT_URI=http://localhost:8501",
                language="bash",
            )


def sidebar() -> None:
    user = st.session_state.user
    with st.sidebar:
        st.subheader(user["name"])
        st.caption(user["email"])
        st.divider()
        st.write("Required upload format")
        st.caption(REQUIRED_REVIEW_COLUMNS["minimum"])
        st.caption(REQUIRED_REVIEW_COLUMNS["recommended"])
        st.divider()
        recent_runs = get_recent_runs(user["id"])
        if recent_runs:
            st.write("Recent analysis runs")
            st.dataframe(pd.DataFrame(recent_runs), use_container_width=True, hide_index=True)
        if st.button("Log out", use_container_width=True):
            st.session_state.jwt = None
            st.session_state.user = None
            st.rerun()


def add_predictions(df: pd.DataFrame) -> tuple[pd.DataFrame, object, dict]:
    model, tuning_info = train_tuned_classifier(df)
    analyzed = df.copy()
    analyzed["predicted_sentiment"] = model.predict(analyzed["clean_review"])
    analyzed["confidence"] = model.predict_proba(analyzed["clean_review"]).max(axis=1) if hasattr(model, "predict_proba") else 0
    return analyzed, model, tuning_info


def record_run_once(file_name: str, analyzed: pd.DataFrame) -> None:
    signature = f"{file_name}:{len(analyzed)}:{round(float(analyzed['rating'].mean()), 4)}"
    if st.session_state.last_recorded_signature == signature:
        return
    positive_rate = float((analyzed["predicted_sentiment"] == "Positive").mean() * 100)
    record_analysis_run(
        st.session_state.user["id"],
        file_name,
        len(analyzed),
        positive_rate,
        float(analyzed["rating"].mean()),
    )
    st.session_state.last_recorded_signature = signature


def analyzer_page() -> None:
    sidebar()
    apply_theme(st.session_state.theme_mode)
    theme_switcher("dashboard")
    st.title(APP_NAME)
    st.caption("A professional Streamlit analytics workspace for SQL-based review insights, text classification, feature selection, model evaluation, and customer satisfaction visualization.")

    uploaded = st.file_uploader("Upload customer reviews CSV or Excel", type=["csv", "xlsx", "xls"])

    with st.expander("Live review import from product URL"):
        product_url = st.text_input("Amazon, Shopify, eBay, or product page URL", placeholder="https://example.com/product")
        if st.button("Fetch live reviews", use_container_width=True):
            try:
                st.session_state.live_review_df = scrape_reviews_from_url(product_url)
                st.session_state.live_review_source = product_url
                st.success(f"Imported {len(st.session_state.live_review_df)} live review candidates.")
            except Exception as exc:
                st.error(f"Could not import reviews from URL: {exc}")

    try:
        if st.session_state.live_review_df is not None and uploaded is None:
            raw_df = st.session_state.live_review_df
            file_name = st.session_state.live_review_source or "live_reviews"
        else:
            raw_df = load_dataset(uploaded)
            file_name = uploaded.name if uploaded else "sample_reviews.csv"
        normalized = normalize_review_dataset(raw_df) #Data cleaning and preprocessing step, including text normalization and validation of required columns. 
    except Exception as exc:
        st.error(str(exc))
        return

    if normalized.empty:
        st.warning("The dataset has no valid review text after preprocessing.")
        return

    analyzed, model, tuning_info = add_predictions(normalized) #Machine learning classification step where a text classification model is trained and used to predict sentiment labels for each review, along with confidence scores.
    aspect_summary, aspect_detail = analyze_aspects(analyzed)
    authenticity = authenticity_scores(analyzed)
    processed_path = save_processed_dataset(analyzed)
    record_run_once(file_name, analyzed)

    positive_rate = (analyzed["predicted_sentiment"] == "Positive").mean() * 100
    negative_rate = (analyzed["predicted_sentiment"] == "Negative").mean() * 100
    avg_rating = analyzed["rating"].mean()

    metric_cols = st.columns(4)
    metric_cols[0].metric("Reviews analyzed", f"{len(analyzed):,}")
    metric_cols[1].metric("Average rating", f"{avg_rating:.2f} / 5")
    metric_cols[2].metric("Positive sentiment", f"{positive_rate:.1f}%")
    metric_cols[3].metric("Negative sentiment", f"{negative_rate:.1f}%")

    tabs = st.tabs(
        [
            "Overview",
            "SQL Insights",
            "ABSA",
            "Support Drafts",
            "Authenticity",
            "Benchmarking",
            "Reports",
            "Classification",
            "Feature Selection",
            "Customer Feedback",
            "Data Preview",
        ]
    )

    with tabs[0]: ##Visualizations of sentiment distribution, category satisfaction, and rating trends to provide a quick overview of customer feedback and product performance.
        left, right = st.columns([1, 1])
        with left:
            st.subheader("Sentiment mix")
            st.plotly_chart(sentiment_donut(analyzed), use_container_width=True)
        with right:
            st.subheader("Category satisfaction")
            st.plotly_chart(category_satisfaction_bar(analyzed), use_container_width=True)
        st.subheader("Rating trend")
        st.plotly_chart(trend_line(analyzed), use_container_width=True)

    with tabs[1]: ##SQL-generated insights into customer satisfaction patterns and product performance.
        st.subheader("SQL-generated customer satisfaction summary")
        sql_summary = satisfaction_summary(analyzed)
        st.dataframe(sql_summary, use_container_width=True, hide_index=True)
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.write("Products needing attention")
            st.dataframe(product_risk_table(analyzed), use_container_width=True, hide_index=True)
        with col_b:
            st.write("Sentiment behavior")
            st.dataframe(keyword_signal_table(analyzed), use_container_width=True, hide_index=True)

        with st.expander("Run a custom SQL query against the reviews table"):
            default_query = "SELECT product_name, category, rating, predicted_sentiment FROM reviews LIMIT 10"
            query = st.text_area("SQL query", default_query, height=120)
            if st.button("Run SQL"):
                try:
                    from data_analysis.sql_insights import run_query

                    st.dataframe(run_query(analyzed, query), use_container_width=True)
                except Exception as exc:
                    st.error(f"SQL error: {exc}")

        with st.expander("Ask with plain English"):
            question = st.text_input(
                "AI data assistant question",
                placeholder="Show me all categories where the average rating dropped below 3 in March",
            )
            if st.button("Translate and run", use_container_width=True):
                if not question.strip():
                    st.warning("Enter a question first.")
                else:
                    try:
                        generated_sql, answer = safe_ai_query(analyzed, question)
                        st.code(generated_sql, language="sql")
                        st.dataframe(answer, use_container_width=True, hide_index=True)
                    except Exception as exc:
                        st.error(f"AI data assistant error: {exc}")

    with tabs[2]: ##Aspect-Based Sentiment Analysis (ABSA) results showing sentiment breakdown by individual product aspects.
        st.subheader("Aspect-Based Sentiment Analysis")
        st.caption("Sentiment is broken down by product aspects such as performance, battery life, quality, shipping, support, price, comfort, design, and ease of use.")
        if aspect_summary.empty:
            st.info("No aspect keywords were detected in the current reviews.")
        else:
            st.dataframe(aspect_summary, use_container_width=True, hide_index=True)
            selected_aspect = st.selectbox("Inspect reviews for aspect", aspect_summary["aspect"].tolist())
            st.dataframe(
                aspect_detail[aspect_detail["aspect"] == selected_aspect][
                    ["product_name", "rating", "aspect_sentiment", "matched_terms", "review_text"]
                ],
                use_container_width=True,
                hide_index=True,
            )

    with tabs[3]: ##Automated customer support response drafts.
        st.subheader("Automated Customer Support Drafts")
        negative_reviews = analyzed[analyzed["predicted_sentiment"] == "Negative"].copy()
        if negative_reviews.empty:
            st.success("No negative reviews detected in the current dataset.")
        else:
            negative_reviews["label"] = negative_reviews.apply(
                lambda row: f"{row.name} | {row['product_name']} | {row['rating']} stars | {row['review_text'][:70]}",
                axis=1,
            )
            selected = st.selectbox("Choose a negative review", negative_reviews["label"].tolist())
            selected_index = int(selected.split("|", 1)[0].strip())
            selected_review = analyzed.loc[selected_index]
            st.write(selected_review["review_text"])
            st.text_area("Draft seller response", draft_support_response(selected_review, aspect_detail), height=190)

    with tabs[4]: ##Heuristic-based review authenticity and fake review detection results.
        st.subheader("Review Authenticity / Fake Review Detector")
        st.caption("A heuristic anomaly model flags duplicate text, short reviews, rating/sentiment mismatches, heavy punctuation, and review bursts.")
        risk_cols = st.columns(3)
        risk_cols[0].metric("High risk", int((authenticity["authenticity_label"] == "High risk").sum()))
        risk_cols[1].metric("Medium risk", int((authenticity["authenticity_label"] == "Medium risk").sum()))
        risk_cols[2].metric("Average risk score", f"{authenticity['authenticity_risk'].mean():.1f}/100")
        st.dataframe(
            authenticity[
                [
                    "product_name",
                    "rating",
                    "predicted_sentiment",
                    "authenticity_risk",
                    "authenticity_label",
                    "risk_reasons",
                    "review_text",
                ]
            ].sort_values("authenticity_risk", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    with tabs[5]:
        st.subheader("Competitor Benchmarking")
        st.caption("Upload one dataset per brand to compare rating, sentiment, and aspect-level weakness side-by-side.")
        brand_files = st.file_uploader(
            "Upload competitor CSV or Excel files",
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=True,
            key="benchmark_uploads",
        )
        if brand_files:
            datasets = {}
            for file in brand_files:
                try:
                    datasets[Path(file.name).stem] = load_dataset(file)
                except Exception as exc:
                    st.warning(f"Skipped {file.name}: {exc}")
            if datasets:
                brand_summary, brand_aspects = benchmark_brands(datasets)
                st.write("Brand performance")
                st.dataframe(brand_summary, use_container_width=True, hide_index=True)
                if not brand_aspects.empty:
                    st.write("Aspect weakness by brand")
                    st.dataframe(brand_aspects, use_container_width=True, hide_index=True)
        else:
            st.info("Upload two or more brand datasets to start a benchmark.")

    with tabs[6]:
        st.subheader("Automated PDF / Email Reporting")
        st.caption("Generate a concise PDF report from the current dashboard, sentiment mix, SQL summary, and ABSA results.")
        report_pdf = generate_report_pdf(analyzed, sql_summary, aspect_summary)
        st.download_button(
            "Generate Report PDF",
            report_pdf,
            file_name="review_analyzer_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        email_to = st.text_input("Stakeholder email", placeholder="manager@example.com")
        subject = "Weekly review analyzer report"
        body = "The latest review analyzer PDF report is ready. Please download it from the dashboard and attach it to this email."
        if email_to:
            st.link_button("Open email draft", f"mailto:{email_to}?subject={subject}&body={body}", use_container_width=True)

    with tabs[7]:
        st.subheader("Text classification model")
        st.write("Target label is derived from rating: 4-5 Positive, 3 Neutral, 1-2 Negative.")
        eval_result = evaluate_model(model, analyzed)
        cols = st.columns(2)
        cols[0].metric("Evaluation accuracy", f"{eval_result.accuracy:.2%}")
        cols[1].metric("Tuning mode", tuning_info["mode"].replace("_", " ").title())
        if tuning_info["best_params"]:
            st.json(tuning_info["best_params"])
        if tuning_info["cv_score"] is not None:
            st.info(f"Best cross-validation score: {tuning_info['cv_score']:.2%}")
        st.plotly_chart(confusion_heatmap(eval_result.confusion, eval_result.labels), use_container_width=True)
        st.dataframe(eval_result.report, use_container_width=True)

    with tabs[8]:
        st.subheader("Important terms selected with TF-IDF and chi-square")
        try:
            terms = top_discriminative_terms(analyzed["clean_review"], analyzed["rating_sentiment"])
            st.dataframe(terms, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"Feature selection needs more text variety: {exc}")

    with tabs[9]:
        st.subheader("Customer Feedback Themes & Insights")
        st.markdown("Automatically extracted themes from customer reviews to identify what customers praise and what they complain about.")
        
        # Extract themes and generate recommendations
        themes = extract_feedback_themes(analyzed, n_themes=4)
        recommendations = generate_recommendations(analyzed, themes)
        keywords = get_top_keywords_by_sentiment(analyzed, top_n=10)
        
        # Display recommendations with color coding
        st.subheader("Action Items")
        if recommendations:
            for rec in recommendations:
                color_map = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Info": "🔵"}
                priority_icon = color_map.get(rec["priority"], "⚪")
                with st.expander(f"{priority_icon} {rec['action']} ({rec['priority']})"):
                    st.write(rec["details"])
        
        # Display themes by sentiment
        col_pos, col_neg, col_neu = st.columns(3)
        
        with col_pos:
            st.markdown("### 🟢 What Customers Love")
            for theme in themes.get("positive", []):
                if "count" in theme:
                    st.markdown(f"**{theme.get('theme', 'N/A')}**")
                    st.caption(f"{theme['count']} reviews ({theme.get('percentage', 0):.0f}%)")
                    if theme.get("keywords"):
                        st.caption(f"Keywords: {', '.join(theme['keywords'][:3])}")
        
        with col_neg:
            st.markdown("### 🔴 What Needs Improvement")
            for theme in themes.get("negative", []):
                if "count" in theme:
                    st.markdown(f"**{theme.get('theme', 'N/A')}**")
                    st.caption(f"{theme['count']} reviews ({theme.get('percentage', 0):.0f}%)")
                    if theme.get("keywords"):
                        st.caption(f"Keywords: {', '.join(theme['keywords'][:3])}")
        
        with col_neu:
            st.markdown("### 🟡 Neutral Feedback")
            for theme in themes.get("neutral", []):
                if "count" in theme:
                    st.markdown(f"**{theme.get('theme', 'N/A')}**")
                    st.caption(f"{theme['count']} reviews ({theme.get('percentage', 0):.0f}%)")
                    if theme.get("keywords"):
                        st.caption(f"Keywords: {', '.join(theme['keywords'][:3])}")
        
        # Top keywords
        st.subheader("Top Keywords by Sentiment")
        kw_col1, kw_col2, kw_col3 = st.columns(3)
        with kw_col1:
            st.markdown("**Positive Words**")
            for kw in keywords.get("positive", []):
                st.caption(f"{kw['word']} ({kw['importance']})")
        with kw_col2:
            st.markdown("**Negative Words**")
            for kw in keywords.get("negative", []):
                st.caption(f"{kw['word']} ({kw['importance']})")
        with kw_col3:
            st.markdown("**Neutral Words**")
            for kw in keywords.get("neutral", []):
                st.caption(f"{kw['word']} ({kw['importance']})")

    with tabs[10]:
        st.subheader("Processed review data")
        st.caption(f"Processed dataset saved to {Path(processed_path).as_posix()}")
        st.dataframe(
            analyzed[
                [
                    "product_name",
                    "category",
                    "rating",
                    "predicted_sentiment",
                    "confidence",
                    "review_date",
                    "review_text",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download analyzed reviews",
            analyzed.to_csv(index=False).encode("utf-8"),
            file_name="analyzed_product_reviews.csv",
            mime="text/csv",
            use_container_width=True,
        )


def main() -> None:
    initialize_state()
    hydrate_user_from_token()
    apply_theme(st.session_state.theme_mode)

    if st.session_state.user:
        analyzer_page()
    else:
        auth_page()


if __name__ == "__main__":
    main()
