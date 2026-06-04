import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import chi2


def top_discriminative_terms(texts, labels, top_n: int = 12) -> pd.DataFrame:
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    features = vectorizer.fit_transform(texts)
    names = vectorizer.get_feature_names_out()
    rows = []

    for label in sorted(set(labels)):
        binary = [1 if item == label else 0 for item in labels]
        scores, _ = chi2(features, binary)
        top_indices = scores.argsort()[-top_n:][::-1]
        for index in top_indices:
            rows.append({"sentiment": label, "term": names[index], "score": round(float(scores[index]), 4)})

    return pd.DataFrame(rows)
