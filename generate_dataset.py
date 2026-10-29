"""Builds a labelled demo dataset (data/emails.csv, data/urls.csv).
For better real-world accuracy replace these CSVs with a public dataset
(same columns) and re-run train_model.py."""
import csv
import random

random.seed(42)
BRANDS = ["PayPal", "Amazon", "Netflix", "Apple", "Microsoft", "HDFC Bank", "SBI", "Google", "Facebook", "DHL"]

P_OPEN = ["Dear customer, your {b} account has been suspended.", "Urgent: unusual activity detected on your {b} account.",
          "Security alert from {b}: your password will expire today.", "Congratulations! You have won a {b} gift card worth $500.",
          "Final notice: your {b} payment failed and your service will be cancelled.", "We could not verify your {b} billing information."]
P_BODY = ["Click the link below to verify your identity immediately.", "Confirm your password and card number within 24 hours.",
          "Failure to respond will result in permanent account closure.", "Log in now to restore access: {u}",
          "Update your details here {u} to claim your reward.", "Act now, this offer expires in one hour!",
          "Provide your bank details and social security number to avoid suspension."]
P_END = ["Thank you, {b} Security Team", "Do not ignore this message.", "Reply with your credentials to resolve this.", "Click here: {u}"]
L_OPEN = ["Hi team, here are the notes from today's project meeting.", "Hello, your order has been shipped and will arrive on Friday.",
          "Please find attached the invoice for last month's consulting work.", "Reminder: the quarterly review is scheduled for Tuesday at 3 PM.",
          "Hi, thanks for registering for our webinar on data engineering.", "Dear students, the assignment deadline has been extended to next Monday.",
          "You requested a password reset. If this was you, use the link on our official site; otherwise ignore this email."]
L_BODY = ["Let me know if you have any questions or need changes.", "The agenda and slides are attached for your reference.",
          "We will discuss the budget, timeline and next steps.", "You can track your parcel from your account dashboard.",
          "Please review the document and share your feedback by Thursday.", "Lunch will be provided, see you in the conference room.",
          "Our support team is available on weekdays if you need any help."]
L_END = ["Best regards, Priya", "Thanks, Rahul", "Kind regards, The HR Team", "Cheers, Ankit", "Regards, Professor Sharma"]
TLD_BAD = ["xyz", "top", "tk", "ml", "click", "info", "icu", "buzz"]
GOOD = ["google.com", "wikipedia.org", "github.com", "amazon.in", "microsoft.com", "python.org", "stackoverflow.com", "bbc.com",
        "nytimes.com", "linkedin.com", "youtube.com", "apple.com", "flipkart.com", "iitb.ac.in", "coursera.org", "mozilla.org",
        "medium.com", "reddit.com", "paypal.com", "netflix.com"]
GPATH = ["", "", "about", "docs/index.html", "questions/12345/how-to-sort", "wiki/Machine_learning", "products/laptops",
         "news/2024/05/world", "in/someone", "search?q=python", "courses/data-science"]
WORDS = ["login", "verify", "secure", "account", "update", "confirm", "signin", "billing", "support"]


def rnd_ip():
    return ".".join(str(random.randint(1, 255)) for _ in range(4))


def url_phish():
    b = random.choice(BRANDS).lower().replace(" ", "")
    w1, w2 = random.sample(WORDS, 2)
    k = random.randint(0, 5)
    sch = random.choice(["http://", "http://", "https://"])
    if k == 0: return f"{sch}{rnd_ip()}/{w1}/{w2}.php"
    if k == 1: return f"{sch}{b}.com.{w1}-{w2}.{random.choice(TLD_BAD)}/{w1}"
    if k == 2: return f"{sch}{b}-{w1}-{w2}.{random.choice(TLD_BAD)}/index.php?id={random.randint(1000, 99999)}&session={random.getrandbits(40):x}"
    if k == 3: return f"{sch}www.{b}.com@{rnd_ip()}/{w1}"
    if k == 4: return f"{sch}secure.{w1}.{b}{random.randint(1, 99)}.{random.choice(TLD_BAD)}/{w2}/{w1}.html"
    return f"{sch}{b}{w1}.{random.choice(['com', 'net', 'online'])}/{w2}?user={random.getrandbits(24):x}"


def url_legit():
    sch = random.choice(["https://", "https://", "https://", "http://"])
    www = random.choice(["www.", "", "en."])
    return f"{sch}{www}{random.choice(GOOD)}/{random.choice(GPATH)}"


def email(phish):
    b, u = random.choice(BRANDS), url_phish() if phish else url_legit()
    o, bo, e = (P_OPEN, P_BODY, P_END) if phish else (L_OPEN, L_BODY, L_END)
    parts = [random.choice(o)] + random.sample(bo, random.randint(1, 3)) + [random.choice(e)]
    return " ".join(parts).format(b=b, u=u)


def write(name, rows):
    random.shuffle(rows)
    with open(f"data/{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text" if name == "emails" else "url", "label"])
        w.writerows(rows)


if __name__ == "__main__":
    write("emails", [(email(True), 1) for _ in range(1500)] + [(email(False), 0) for _ in range(1500)])
    write("urls", [(url_phish(), 1) for _ in range(2000)] + [(url_legit(), 0) for _ in range(2000)])
    print("Datasets written to data/emails.csv and data/urls.csv")
