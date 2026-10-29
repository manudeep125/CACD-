"""URL feature extraction shared by training and the Flask app."""
import math
import re
from urllib.parse import urlparse

SUSPICIOUS_WORDS = ["login", "verify", "secure", "account", "update", "bank", "confirm",
                    "signin", "password", "wallet", "suspend", "billing", "support", "free"]
SUSPICIOUS_TLDS = {"xyz", "top", "tk", "ml", "ga", "cf", "gq", "click", "work", "info", "buzz", "icu"}
FEATURE_NAMES = ["url_length", "host_length", "num_dots", "num_hyphens", "num_digits", "has_at",
                 "has_ip", "is_https", "num_subdomains", "suspicious_words", "path_length",
                 "num_params", "suspicious_tld", "entropy", "double_slash_in_path", "num_special"]


def normalize_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "http://" + url
    return url


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    return -sum((s.count(c) / len(s)) * math.log2(s.count(c) / len(s)) for c in set(s))


def extract_features(url: str) -> list:
    url = normalize_url(url)
    p = urlparse(url)
    host = (p.hostname or "").lower()
    low = url.lower()
    labels = host.split(".")
    tld = labels[-1] if labels else ""
    return [
        len(url), len(host), url.count("."), url.count("-"),
        sum(c.isdigit() for c in url), int("@" in url),
        int(bool(re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host))),
        int(p.scheme == "https"), max(len(labels) - 2, 0),
        sum(w in low for w in SUSPICIOUS_WORDS), len(p.path),
        len(p.query.split("&")) if p.query else 0,
        int(tld in SUSPICIOUS_TLDS), round(_entropy(host), 3),
        int("//" in p.path), len(re.findall(r"[^\w./:-]", url)),
    ]


def explain_url(url: str) -> list:
    f = dict(zip(FEATURE_NAMES, extract_features(url)))
    r = []
    if f["has_ip"]: r.append("Uses a raw IP address instead of a domain name")
    if f["has_at"]: r.append("Contains '@', which can hide the real destination")
    if not f["is_https"]: r.append("Does not use HTTPS")
    if f["suspicious_words"] >= 2: r.append(f"Contains {f['suspicious_words']} suspicious keywords (login, verify, secure...)")
    if f["num_hyphens"] >= 3: r.append("Has many hyphens in the address")
    if f["num_subdomains"] >= 3: r.append("Has many subdomains (possible brand impersonation)")
    if f["suspicious_tld"]: r.append("Uses a top-level domain often abused by phishers")
    if f["url_length"] > 75: r.append("Unusually long URL")
    return r or ["No obvious suspicious patterns found"]
