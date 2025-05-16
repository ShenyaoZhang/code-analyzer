#!/usr/bin/env python
# coding: utf-8

import subprocess
import json
import uuid
import re
import sys
from ml_predictor import CodeQualityPredictor  # Live model
from recommendation_engine import CodeRecommendationEngine
from code_metrics import CodeMetricsCalculator

class CodeAnalyzer:
    def __init__(self):
        self.recommender = CodeRecommendationEngine()
        self.metrics = CodeMetricsCalculator()
        self.tools = {
            "pylint": ["pylint", "--output-format=json"],
            "flake8": ["flake8", "--format=%(row)d:%(col)d:%(code)s:%(text)s"]
        }
        # Use your deployed SageMaker endpoint name here
        self.predictor = CodeQualityPredictor("huggingface-pytorch-inference-2025-05-16-00-58-00-996")
    

    def run_tool(self, tool, file_path):
        command = self.tools.get(tool) + [file_path]
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=False
            )
            return result.stdout
        except Exception as e:
            print(f"[ERROR] Running {tool} failed: {e}")
            return ""

    def parse_flake8(self, output, file_path):
        results = []
        for line in output.strip().splitlines():
            parts = line.split(":")
            if len(parts) >= 4:
                results.append({
                    "type": "style",
                    "severity": "warning",
                    "line": int(parts[0]),
                    "column": int(parts[1]),
                    "message": ":".join(parts[3:]).strip(),
                    "tool": "flake8",
                    "rule": parts[2]
                })
        return results

    def parse_pylint(self, output, file_path):
        try:
            json_output = json.loads(output)
            results = []
            for item in json_output:
                results.append({
                    "type": item.get("type"),
                    "severity": item.get("type"),
                    "line": item.get("line"),
                    "column": item.get("column"),
                    "message": item.get("message"),
                    "tool": "pylint",
                    "rule": item.get("symbol")
                })
            return results
        except json.JSONDecodeError:
            print("[ERROR] Failed to parse pylint JSON output")
            return []

    def run_bandit(self, file_path):
        try:
            result = subprocess.run(
                ["bandit", "-f", "json", "-q", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=False
            )
            return result.stdout
        except Exception as e:
            print(f"[ERROR] Running Bandit failed: {e}")
            return ""

    def parse_bandit(self, output, file_path):
        results = []
        try:
            data = json.loads(output)
            for issue in data.get("results", []):
                results.append({
                    "type": "security",
                    "severity": issue.get("issue_severity", "LOW").lower(),
                    "line": issue.get("line_number"),
                    "column": 0,
                    "message": issue.get("issue_text"),
                    "tool": "bandit",
                    "rule": issue.get("test_id")
                })
        except json.JSONDecodeError:
            print("[ERROR] Failed to parse Bandit JSON output")
        return results

    def analyze_python(self, file_path):
        results = []

        flake8_output = self.run_tool("flake8", file_path)
        results.extend(self.parse_flake8(flake8_output, file_path))

        pylint_output = self.run_tool("pylint", file_path)
        results.extend(self.parse_pylint(pylint_output, file_path))

        bandit_output = self.run_bandit(file_path)
        results.extend(self.parse_bandit(bandit_output, file_path))

        # ML + Metrics
        with open(file_path, "r") as f:
            code = f.read()

        quality_score = self.predictor.predict_quality(code)
        maintainability = self.metrics.calculate_maintainability(code)

        return self.format_results(results, file_path, quality_score, maintainability)

    def format_results(self, results, file_path, quality_score, maintainability, duplicates=None):
        formatted = {
            "analysis_id": str(uuid.uuid4()),
            "file_path": file_path,
            "quality_score": quality_score,
            "maintainability": maintainability,
            "issues": results,
            "recommendations": self.recommender.get_recommendations(results)
        }
        if duplicates:
            formatted["duplicates"] = duplicates
        return formatted
    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <file_to_analyze>")
        sys.exit(1)

    file_to_analyze = sys.argv[1]
    analyzer = CodeAnalyzer()
    result = analyzer.analyze_python(file_to_analyze)
    print(json.dumps(result, indent=2))



