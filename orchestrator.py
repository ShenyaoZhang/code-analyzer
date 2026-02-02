import os
import json
import logging
from analyzer import CodeAnalyzer
from duplication_detector import DuplicationDetector
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        logger.info(f"Starting repository analysis: {repo_path}")
        
        if not os.path.exists(repo_path):
            logger.error(f"Repository path does not exist: {repo_path}")
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        if not os.path.isdir(repo_path):
            logger.error(f"Path is not a directory: {repo_path}")
            raise ValueError(f"Path is not a directory: {repo_path}")
        
        results = {}
        file_map = {}

        # Step 1: Analyze files and gather code
        files = self.get_files(repo_path)
        logger.info(f"Found {len(files)} files to process")
        
        for file_path in files:
            language = self.detect_language(file_path)
            if language == "python":
                logger.info(f"Analyzing {file_path}...")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code = f.read()
                        file_map[file_path] = code
                        result = self.analyzer.analyze_python(file_path)
                        results[file_path] = result
                except UnicodeDecodeError:
                    logger.warning(f"Unable to decode {file_path} as UTF-8, skipping")
                except Exception as e:
                    logger.error(f"Failed to analyze {file_path}: {e}", exc_info=True)
                    results[file_path] = {
                        "error": str(e),
                        "file_path": file_path
                    }
            else:
                logger.debug(f"Skipping {file_path} — unsupported language")

        # Step 2: Detect duplication
        logger.info("Detecting code duplication...")
        try:
            duplicates = self.dup_checker.find_duplicates(file_map)
            logger.info(f"Found {len(duplicates)} duplicate code blocks")
        except Exception as e:
            logger.error(f"Duplication detection failed: {e}")
            duplicates = []

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

        logger.info(f"Repository analysis complete: {len(results)} files analyzed")
        return results



if __name__ == "__main__":
    repo_path = "sample_repo"
    orchestrator = AnalysisOrchestrator()
    full_results = orchestrator.analyze_repository(repo_path)

    print("\n=== Full Analysis Output ===")
    print(json.dumps(full_results, indent=2))
