#!/usr/bin/env python
# coding: utf-8

import subprocess
import json
import uuid
import re
import sys
import os
import logging
from ml_predictor import CodeQualityPredictor  # Live model
from recommendation_engine import CodeRecommendationEngine
from code_metrics import CodeMetricsCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CodeAnalyzer:
    def __init__(self):
        self.recommender = CodeRecommendationEngine()
        self.metrics = CodeMetricsCalculator()
        self.tools = {
            "pylint": ["pylint", "--output-format=json"],
            "flake8": ["flake8", "--format=%(row)d:%(col)d:%(code)s:%(text)s"]
        }
        # Use environment variable for SageMaker endpoint
        endpoint_name = os.getenv('SAGEMAKER_ENDPOINT_NAME', 'huggingface-pytorch-inference-2025-05-16-00-58-00-996')
        self.predictor = CodeQualityPredictor(endpoint_name)
        logger.info(f"Initialized CodeAnalyzer with endpoint: {endpoint_name}")
    

    def run_tool(self, tool, file_path):
        command = self.tools.get(tool) + [file_path]
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=False,
                timeout=30
            )
            logger.debug(f"Ran {tool} on {file_path}, exit code: {result.returncode}")
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout running {tool} on {file_path}")
            return ""
        except FileNotFoundError:
            logger.error(f"{tool} not found. Please ensure it is installed.")
            return ""
        except Exception as e:
            logger.error(f"Error running {tool} on {file_path}: {e}")
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
        if not output.strip():
            return []
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
            logger.debug(f"Parsed {len(results)} pylint issues from {file_path}")
            return results
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse pylint JSON output for {file_path}: {e}")
            return []

    def run_bandit(self, file_path):
        try:
            result = subprocess.run(
                ["bandit", "-f", "json", "-q", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=False,
                timeout=30
            )
            logger.debug(f"Ran bandit on {file_path}, exit code: {result.returncode}")
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout running bandit on {file_path}")
            return ""
        except FileNotFoundError:
            logger.error("Bandit not found. Please ensure it is installed.")
            return ""
        except Exception as e:
            logger.error(f"Error running bandit on {file_path}: {e}")
            return ""

    def parse_bandit(self, output, file_path):
        results = []
        if not output.strip():
            return []
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
            logger.debug(f"Parsed {len(results)} bandit issues from {file_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse bandit JSON output for {file_path}: {e}")
        return results

    def analyze_python(self, file_path):
        logger.info(f"Starting analysis of {file_path}")
        results = []

        # Run static analysis tools
        flake8_output = self.run_tool("flake8", file_path)
        results.extend(self.parse_flake8(flake8_output, file_path))

        pylint_output = self.run_tool("pylint", file_path)
        results.extend(self.parse_pylint(pylint_output, file_path))

        bandit_output = self.run_bandit(file_path)
        results.extend(self.parse_bandit(bandit_output, file_path))

        # ML + Metrics
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
        except UnicodeDecodeError:
            logger.warning(f"Unable to decode {file_path} as UTF-8, trying latin-1")
            with open(file_path, "r", encoding="latin-1") as f:
                code = f.read()
        except IOError as e:
            logger.error(f"Failed to read {file_path}: {e}")
            raise

        try:
            quality_score = self.predictor.predict_quality(code)
        except Exception as e:
            logger.error(f"ML prediction failed for {file_path}: {e}")
            quality_score = 0.0

        maintainability = self.metrics.calculate_maintainability(code)
        
        logger.info(f"Completed analysis of {file_path}: {len(results)} issues found")
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



