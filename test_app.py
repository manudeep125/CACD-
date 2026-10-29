import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app


class PhishGuardTests(unittest.TestCase):
    def setUp(self): self.c = app.test_client()

    def test_phishing_email(self):
        r = self.c.post("/api/analyze/email", json={"text": "Urgent: your PayPal account has been suspended. Verify your password immediately at http://paypal-login.xyz"})
        self.assertEqual(r.get_json()["label"], "Phishing")

    def test_safe_email(self):
        r = self.c.post("/api/analyze/email", json={"text": "Hi team, here are the notes from today's project meeting. Thanks, Rahul"})
        self.assertEqual(r.get_json()["label"], "Safe")

    def test_phishing_url(self):
        self.assertEqual(self.c.post("/api/analyze/url", json={"url": "http://192.168.4.5/secure-login/verify.php"}).get_json()["label"], "Phishing")

    def test_safe_url(self):
        self.assertEqual(self.c.post("/api/analyze/url", json={"url": "https://www.wikipedia.org/wiki/Machine_learning"}).get_json()["label"], "Safe")

    def test_validation(self):
        self.assertEqual(self.c.post("/api/analyze/email", json={"text": "short"}).status_code, 400)
        self.assertEqual(self.c.post("/api/analyze/url", json={"url": "not a url"}).status_code, 400)
        self.assertEqual(self.c.post("/api/analyze/url", data="garbage").status_code, 400)

    def test_stats_and_history(self):
        self.assertIn("total", self.c.get("/api/stats").get_json())
        self.assertIsInstance(self.c.get("/api/history").get_json(), list)
        for p in ("/", "/dashboard", "/history"):
            self.assertEqual(self.c.get(p).status_code, 200)


if __name__ == "__main__":
    unittest.main()
