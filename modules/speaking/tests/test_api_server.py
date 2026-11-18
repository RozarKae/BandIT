"""
Unit tests for the IELTS API Server.
"""

import unittest
import threading
import http.client
import json
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api_server import run_server


class TestIELTSApiServer(unittest.TestCase):
    server_thread = None
    port = 8899

    @classmethod
    def setUpClass(cls):
        # Run API server in background thread
        cls.server_thread = threading.Thread(target=run_server, args=(cls.port,), daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

    def _make_request(self, method: str, path: str, body: dict = None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port)
        headers = {"Content-Type": "application/json"} if body else {}
        body_str = json.dumps(body) if body else None
        conn.request(method, path, body=body_str, headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        conn.close()
        return res.status, json.loads(data) if data else {}

    def test_health_and_topics(self):
        status, data = self._make_request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")

        status, data = self._make_request("GET", "/api/topics")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(data["topics"]), 3)

    def test_session_lifecycle_and_scoring(self):
        # 1. Start Session
        status, start_data = self._make_request("POST", "/api/sessions/start", {
            "test_set_id": "ielts_set_tech_01",
            "candidate_name": "David"
        })
        self.assertEqual(status, 200)
        session_id = start_data["session_id"]
        self.assertIn("action", start_data)

        # 2. Next turn (Candidate responds to ID check)
        status, turn_data = self._make_request("POST", "/api/sessions/next", {
            "session_id": session_id,
            "candidate_text": "My name is David Smith, please call me David.",
            "duration_seconds": 4.5
        })
        self.assertEqual(status, 200)
        self.assertEqual(turn_data["action"]["stage"], "PART1_QUESTIONS")

        # 3. Next turn (Candidate answers Part 1 Question)
        status, turn_data = self._make_request("POST", "/api/sessions/next", {
            "session_id": session_id,
            "candidate_text": "I use mobile apps primarily for scheduling, fitness tracking, and navigation. They are indispensable for keeping my daily schedule organized.",
            "duration_seconds": 22.0
        })
        self.assertEqual(status, 200)

        # 4. Request Score
        status, score_data = self._make_request("POST", "/api/sessions/score", {
            "session_id": session_id
        })
        self.assertEqual(status, 200)
        self.assertIn("scorecard", score_data)
        self.assertIn("overall_band", score_data["scorecard"])
        self.assertIn("markdown_report", score_data)


if __name__ == "__main__":
    unittest.main()
