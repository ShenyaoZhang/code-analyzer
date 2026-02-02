import unittest
from fastapi.testclient import TestClient
import sys
import os

# Mock the SageMaker predictor before importing the API
class MockPredictor:
    def predict(self, payload):
        return [[
            [0.1] * 768  # Mock embedding
        ]]

sys.modules['ml_predictor'].CodeQualityPredictor = lambda x: type('MockPredictor', (), {'predict_quality': lambda self, code: 0.75})()

from analysis_api import app


class TestAnalysisAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("service", data)
        self.assertIn("version", data)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")

    def test_analyze_empty_path(self):
        response = self.client.post("/analyze", json={"repo_path": ""})
        self.assertEqual(response.status_code, 422)  # Validation error

    def test_analyze_invalid_github_url(self):
        response = self.client.post(
            "/analyze",
            json={"repo_path": "https://invalid-url.com/repo"}
        )
        self.assertEqual(response.status_code, 422)  # Validation error

    def test_analyze_malicious_path(self):
        response = self.client.post(
            "/analyze",
            json={"repo_path": "/etc/passwd"}
        )
        self.assertEqual(response.status_code, 422)  # Should be blocked

    def test_analyze_path_traversal(self):
        response = self.client.post(
            "/analyze",
            json={"repo_path": "../../../etc/passwd"}
        )
        self.assertEqual(response.status_code, 422)  # Should be blocked

    def test_analyze_nonexistent_local_path(self):
        response = self.client.post(
            "/analyze",
            json={"repo_path": "/nonexistent/path/to/repo"}
        )
        self.assertEqual(response.status_code, 400)  # Bad request

    def test_analyze_valid_github_url_format(self):
        # This will fail to clone, but should pass validation
        response = self.client.post(
            "/analyze",
            json={"repo_path": "https://github.com/user/repo"}
        )
        # Will fail at clone stage (400) not validation (422)
        self.assertIn(response.status_code, [400, 408, 500])

    def test_api_docs_available(self):
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)

    def test_openapi_schema(self):
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertIn("openapi", schema)
        self.assertIn("paths", schema)

    def test_cors_headers(self):
        response = self.client.options(
            "/analyze",
            headers={"Origin": "http://localhost:3000"}
        )
        # Should have CORS headers
        self.assertIn("access-control-allow-origin", response.headers)


if __name__ == '__main__':
    unittest.main()

