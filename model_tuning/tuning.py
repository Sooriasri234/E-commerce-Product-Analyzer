import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline


def base_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def train_tuned_classifier(df: pd.DataFrame):
    labels = df["rating_sentiment"].value_counts()
    pipeline = base_pipeline()

    if len(labels) < 2 or len(df) < 10 or labels.min() < 2:
        pipeline.fit(df["clean_review"], df["rating_sentiment"])
        return pipeline, {"mode": "baseline", "best_params": {}, "cv_score": None}

    grid = GridSearchCV(
        pipeline,
        param_grid={
            "tfidf__max_features": [750, 1500, 3000],
            "classifier__C": [0.5, 1.0, 2.0],
        },
        cv=2,
        scoring="accuracy",
        n_jobs=1,
    )
    grid.fit(df["clean_review"], df["rating_sentiment"])
    return grid.best_estimator_, {
        "mode": "grid_search",
        "best_params": grid.best_params_,
        "cv_score": round(float(grid.best_score_), 4),
    }
