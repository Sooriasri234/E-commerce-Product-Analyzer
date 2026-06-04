import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def sentiment_donut(df: pd.DataFrame) -> go.Figure:
    counts = df["predicted_sentiment"].value_counts().reset_index()
    counts.columns = ["sentiment", "count"]
    fig = px.pie(
        counts,
        names="sentiment",
        values="count",
        hole=0.55,
        color="sentiment",
        color_discrete_map={"Positive": "#1f9d75", "Neutral": "#d89c20", "Negative": "#d64545"},
    )
    fig.update_layout(margin=dict(t=24, b=20, l=20, r=20), showlegend=True)
    return fig


def category_satisfaction_bar(df: pd.DataFrame) -> go.Figure:
    grouped = (
        df.groupby("category", as_index=False)
        .agg(avg_rating=("rating", "mean"), reviews=("review_text", "count"))
        .sort_values("avg_rating", ascending=False)
    )
    fig = px.bar(grouped, x="category", y="avg_rating", color="reviews", text_auto=".2f", color_continuous_scale="Teal")
    fig.update_layout(xaxis_title="Category", yaxis_title="Average rating", margin=dict(t=24, b=20, l=20, r=20))
    fig.update_yaxes(range=[0, 5])
    return fig


def trend_line(df: pd.DataFrame) -> go.Figure:
    trend = (
        df.assign(review_month=df["review_date"].dt.to_period("M").astype(str))
        .groupby("review_month", as_index=False)
        .agg(avg_rating=("rating", "mean"), reviews=("review_text", "count"))
    )
    fig = px.line(trend, x="review_month", y="avg_rating", markers=True, hover_data=["reviews"])
    fig.update_layout(xaxis_title="Month", yaxis_title="Average rating", margin=dict(t=24, b=20, l=20, r=20))
    fig.update_yaxes(range=[0, 5])
    return fig


def confusion_heatmap(matrix, labels) -> go.Figure:
    fig = px.imshow(matrix, x=labels, y=labels, text_auto=True, color_continuous_scale="Blues")
    fig.update_layout(xaxis_title="Predicted", yaxis_title="Actual", margin=dict(t=24, b=20, l=20, r=20))
    return fig
