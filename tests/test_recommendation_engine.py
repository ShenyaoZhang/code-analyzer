import unittest
from recommendation_engine import CodeRecommendationEngine


class TestCodeRecommendationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CodeRecommendationEngine()

    def test_get_recommendations_empty(self):
        issues = []
        recommendations = self.engine.get_recommendations(issues)
        self.assertEqual(len(recommendations), 0)

    def test_get_recommendations_no_matching_rules(self):
        issues = [
            {"line": 1, "tool": "pylint", "rule": "unknown-rule", "message": "Unknown issue"}
        ]
        recommendations = self.engine.get_recommendations(issues)
        self.assertEqual(len(recommendations), 0)

    def test_get_recommendations_line_length(self):
        issues = [
            {"line": 10, "tool": "flake8", "rule": "E501", "message": "Line too long"}
        ]
        recommendations = self.engine.get_recommendations(issues)
        
        self.assertEqual(len(recommendations), 1)
        rec = recommendations[0]
        self.assertEqual(rec['line'], 10)
        self.assertEqual(rec['tool'], 'flake8')
        self.assertEqual(rec['rule'], 'E501')
        self.assertIn('Break long lines', rec['suggestion'])

    def test_get_recommendations_missing_docstring(self):
        issues = [
            {"line": 1, "tool": "pylint", "rule": "missing-docstring", "message": "Missing docstring"}
        ]
        recommendations = self.engine.get_recommendations(issues)
        
        self.assertEqual(len(recommendations), 1)
        self.assertIn('docstring', recommendations[0]['suggestion'].lower())

    def test_get_recommendations_eval_usage(self):
        issues = [
            {"line": 5, "tool": "bandit", "rule": "B307", "message": "Use of eval"}
        ]
        recommendations = self.engine.get_recommendations(issues)
        
        self.assertEqual(len(recommendations), 1)
        rec = recommendations[0]
        self.assertIn('eval', rec['suggestion'].lower())
        self.assertIn('literal_eval', rec['suggestion'])

    def test_get_recommendations_hardcoded_password(self):
        issues = [
            {"line": 3, "tool": "bandit", "rule": "B105", "message": "Hardcoded password"}
        ]
        recommendations = self.engine.get_recommendations(issues)
        
        self.assertEqual(len(recommendations), 1)
        rec = recommendations[0]
        self.assertIn('password', rec['suggestion'].lower())
        self.assertIn('environment', rec['suggestion'].lower())

    def test_get_recommendations_multiple_issues(self):
        issues = [
            {"line": 1, "tool": "flake8", "rule": "E501", "message": "Line too long"},
            {"line": 5, "tool": "pylint", "rule": "missing-docstring", "message": "Missing docstring"},
            {"line": 10, "tool": "bandit", "rule": "B307", "message": "Use of eval"},
            {"line": 20, "tool": "flake8", "rule": "unknown", "message": "Unknown"}
        ]
        recommendations = self.engine.get_recommendations(issues)
        
        # Should get 3 recommendations (last one has no matching rule)
        self.assertEqual(len(recommendations), 3)

    def test_recommendation_structure(self):
        issues = [
            {"line": 10, "tool": "flake8", "rule": "E501", "message": "Line too long"}
        ]
        recommendations = self.engine.get_recommendations(issues)
        
        rec = recommendations[0]
        self.assertIn('line', rec)
        self.assertIn('tool', rec)
        self.assertIn('rule', rec)
        self.assertIn('suggestion', rec)
        self.assertIn('message', rec)

    def test_recommendation_map_coverage(self):
        # Test that all rules in the map are valid
        for rule, suggestion in self.engine.recommendation_map.items():
            self.assertIsInstance(rule, str)
            self.assertIsInstance(suggestion, str)
            self.assertGreater(len(suggestion), 0)


if __name__ == '__main__':
    unittest.main()

