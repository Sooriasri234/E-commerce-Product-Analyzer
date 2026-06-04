from dataclasses import dataclass

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


@dataclass
class EvaluationResult:
    accuracy: float
    report: pd.DataFrame
    confusion: list[list[int]]
    labels: list[str]


def evaluate_model(pipeline, df: pd.DataFrame) -> EvaluationResult:
    labels = sorted(df["rating_sentiment"].unique().tolist())
    label_counts = df["rating_sentiment"].value_counts()
    if len(df) < 8 or len(labels) < 2 or label_counts.min() < 2:
        predictions = pipeline.predict(df["clean_review"])
        return EvaluationResult(
            accuracy=float(accuracy_score(df["rating_sentiment"], predictions)),
            report=pd.DataFrame(classification_report(df["rating_sentiment"], predictions, output_dict=True)).transpose(),
            confusion=confusion_matrix(df["rating_sentiment"], predictions, labels=labels).tolist(),
            labels=labels,
        )

    x_train, x_test, y_train, y_test = train_test_split(
        df["clean_review"],
        df["rating_sentiment"],
        test_size=0.25,
        random_state=42,
        stratify=df["rating_sentiment"],
    )
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    return EvaluationResult(
        accuracy=float(accuracy_score(y_test, predictions)),
        report=pd.DataFrame(classification_report(y_test, predictions, output_dict=True, zero_division=0)).transpose(),
        confusion=confusion_matrix(y_test, predictions, labels=labels).tolist(),
        labels=labels,
    )
