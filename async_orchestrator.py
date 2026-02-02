import os
import json
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from analyzer import CodeAnalyzer
from duplication_detector import DuplicationDetector
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AsyncAnalysisOrchestrator:
    """
    Async version of AnalysisOrchestrator for better performance.
    Uses asyncio and thread pools to analyze multiple files concurrently.
    """
    
    def __init__(self, max_workers=4):
        self.analyzer = CodeAnalyzer()
        self.dup_checker = DuplicationDetector(min_lines=3)
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

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
    
    async def analyze_file_async(self, file_path):
        """Analyze a single file asynchronously"""
        loop = asyncio.get_event_loop()
        try:
            # Run CPU-bound analysis in thread pool
            result = await loop.run_in_executor(
                self.executor,
                self.analyzer.analyze_python,
                file_path
            )
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            return file_path, result, code
        except UnicodeDecodeError:
            logger.warning(f"Unable to decode {file_path} as UTF-8, skipping")
            return file_path, None, None
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}", exc_info=True)
            return file_path, {"error": str(e), "file_path": file_path}, None
    
    async def analyze_repository(self, repo_path):
        """
        Analyze repository asynchronously with concurrent file processing.
        
        Args:
            repo_path (str): Path to repository
            
        Returns:
            dict: Analysis results for all files
        """
        logger.info(f"Starting async repository analysis: {repo_path}")
        
        if not os.path.exists(repo_path):
            logger.error(f"Repository path does not exist: {repo_path}")
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        if not os.path.isdir(repo_path):
            logger.error(f"Path is not a directory: {repo_path}")
            raise ValueError(f"Path is not a directory: {repo_path}")
        
        results = {}
        file_map = {}

        # Step 1: Get all files
        all_files = self.get_files(repo_path)
        python_files = [f for f in all_files if self.detect_language(f) == "python"]
        
        logger.info(f"Found {len(python_files)} Python files to analyze concurrently")

        # Step 2: Analyze files concurrently
        if python_files:
            tasks = [self.analyze_file_async(file_path) for file_path in python_files]
            
            # Use asyncio.gather to run all analyses concurrently
            analysis_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for item in analysis_results:
                if isinstance(item, Exception):
                    logger.error(f"Analysis task failed: {item}")
                    continue
                
                file_path, result, code = item
                if result is not None:
                    results[file_path] = result
                if code is not None:
                    file_map[file_path] = code

        # Step 3: Detect duplication (run in executor as it's CPU-bound)
        logger.info("Detecting code duplication...")
        try:
            loop = asyncio.get_event_loop()
            duplicates = await loop.run_in_executor(
                self.executor,
                self.dup_checker.find_duplicates,
                file_map
            )
            logger.info(f"Found {len(duplicates)} duplicate code blocks")
        except Exception as e:
            logger.error(f"Duplication detection failed: {e}")
            duplicates = []

        # Step 4: Map file path to duplicates
        dup_map = defaultdict(list)
        for dup in duplicates:
            dup_entry = {
                "source": dup['original_in'],
                "line_range": dup['line_range'],
                "snippet": dup['snippet']
            }
            dup_map[dup['duplicate_in']].append(dup_entry)

        # Step 5: Add duplicates to results
        for file_path, result in results.items():
            if file_path in dup_map:
                result["duplicates"] = dup_map[file_path]

        logger.info(f"Async repository analysis complete: {len(results)} files analyzed")
        return results

    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# Convenience function for synchronous usage
def analyze_repository_async(repo_path, max_workers=4):
    """
    Convenience function to run async analysis from sync code.
    
    Args:
        repo_path (str): Path to repository
        max_workers (int): Maximum concurrent workers
        
    Returns:
        dict: Analysis results
    """
    orchestrator = AsyncAnalysisOrchestrator(max_workers=max_workers)
    return asyncio.run(orchestrator.analyze_repository(repo_path))


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        repo_path = "sample_repo"
    
    results = analyze_repository_async(repo_path)
    
    print("\n=== Async Analysis Output ===")
    print(json.dumps(results, indent=2))

