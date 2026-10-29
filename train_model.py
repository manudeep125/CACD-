"""Trains the email (TF-IDF + Logistic Regression) and URL (Random Forest) models."""
import json
import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from features import extract_features


def metrics(y_true, y_pred):
    return {"accuracy": round(accuracy_score(y_true, y_pred), 4), "precision": round(precision_score(y_true, y_pred), 4),
            "recall": round(recall_score(y_true, y_pred), 4), "f1": round(f1_score(y_true, y_pred), 4)}


def main():
    os.makedirs("models", exist_ok=True)
    if not os.path.exists("data/emails.csv"):
        import generate_dataset as g
        g.write("emails", [(g.email(True), 1) for _ in range(1500)] + [(g.email(False), 0) for _ in range(1500)])
        g.write("urls", [(g.url_phish(), 1) for _ in range(2000)] + [(g.url_legit(), 0) for _ in range(2000)])

    e = pd.read_csv("data/emails.csv").dropna()
    Xtr, Xte, ytr, yte = train_test_split(e["text"], e["label"], test_size=0.2, random_state=42, stratify=e["label"])
    email_model = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=5000)),
                            ("clf", LogisticRegression(max_iter=1000))]).fit(Xtr, ytr)
    em = metrics(yte, email_model.predict(Xte))

    u = pd.read_csv("data/urls.csv").dropna()
    X = [extract_features(x) for x in u["url"]]
    Xtr, Xte, ytr, yte = train_test_split(X, u["label"], test_size=0.2, random_state=42, stratify=u["label"])
    url_model = RandomForestClassifier(n_estimators=150, random_state=42).fit(Xtr, ytr)
    um = metrics(yte, url_model.predict(Xte))

    joblib.dump(email_model, "models/email_model.joblib")
    joblib.dump(url_model, "models/url_model.joblib")
    with open("models/metrics.json", "w") as f:
        json.dump({"email": em, "url": um}, f, indent=2)
    print("Email model:", em)
    print("URL model:  ", um)


if __name__ == "__main__":
    main()
