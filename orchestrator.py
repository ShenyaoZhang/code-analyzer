import os
import json
from analyzer import CodeAnalyzer
from duplication_detector import DuplicationDetector
from collections import defaultdict

class AnalysisOrchestrator:
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.dup_checker = DuplicationDetector(min_lines=3)

    def detect_language(self, file_path):
        if file_path.endswith(".py"):
            return "python"
        return None

    def get_files(self, repo_path):
        file_list = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                full_path = os.path.join(root, file)
                file_list.append(full_path)
        return file_list
    
    def analyze_repository(self, repo_path):
        results = {}
        file_map = {}

        # Step 1: Analyze files and gather code
        for file_path in self.get_files(repo_path):
            language = self.detect_language(file_path)
            if language == "python":
                print(f"Analyzing {file_path}...")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code = f.read()
                        file_map[file_path] = code
                        result = self.analyzer.analyze_python(file_path)
                        results[file_path] = result
                except Exception as e:
                    print(f"Failed to analyze {file_path}: {e}")
            else:
                print(f"Skipping {file_path} — unsupported language")

        # Step 2: Detect duplication
        duplicates = self.dup_checker.find_duplicates(file_map)

        # Step 3: Map file path to duplicates
        dup_map = defaultdict(list)
        for dup in duplicates:
            dup_entry = {
                "source": dup['original_in'],
                "line_range": dup['line_range'],
                "snippet": dup['snippet']
            }
            dup_map[dup['duplicate_in']].append(dup_entry)

        # Step 4: Add duplicates to results
        for file_path, result in results.items():
            if file_path in dup_map:
                result["duplicates"] = dup_map[file_path]

        return results



if __name__ == "__main__":
    repo_path = "sample_repo"
    orchestrator = AnalysisOrchestrator()
    full_results = orchestrator.analyze_repository(repo_path)

    print("\n=== Full Analysis Output ===")
    print(json.dumps(full_results, indent=2))
