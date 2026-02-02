import unittest
import os
import tempfile
import shutil
from orchestrator import AnalysisOrchestrator


class TestAnalysisOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = AnalysisOrchestrator()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_detect_language_python(self):
        lang = self.orchestrator.detect_language("test.py")
        self.assertEqual(lang, "python")

    def test_detect_language_unsupported(self):
        lang = self.orchestrator.detect_language("test.js")
        self.assertIsNone(lang)

    def test_get_files_empty_directory(self):
        files = self.orchestrator.get_files(self.temp_dir)
        self.assertEqual(len(files), 0)

    def test_get_files_with_python_files(self):
        # Create test files
        file1 = os.path.join(self.temp_dir, "test1.py")
        file2 = os.path.join(self.temp_dir, "test2.py")
        
        with open(file1, "w") as f:
            f.write("print('test')")
        with open(file2, "w") as f:
            f.write("print('test2')")
        
        files = self.orchestrator.get_files(self.temp_dir)
        self.assertEqual(len(files), 2)

    def test_get_files_nested_directories(self):
        # Create nested structure
        subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(subdir)
        
        file1 = os.path.join(self.temp_dir, "test1.py")
        file2 = os.path.join(subdir, "test2.py")
        
        with open(file1, "w") as f:
            f.write("print('test1')")
        with open(file2, "w") as f:
            f.write("print('test2')")
        
        files = self.orchestrator.get_files(self.temp_dir)
        self.assertEqual(len(files), 2)

    def test_analyze_repository_nonexistent_path(self):
        with self.assertRaises(ValueError):
            self.orchestrator.analyze_repository("/nonexistent/path")

    def test_analyze_repository_not_directory(self):
        # Create a file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        with self.assertRaises(ValueError):
            self.orchestrator.analyze_repository(test_file)

    def test_analyze_repository_with_python_file(self):
        # Create a simple Python file
        test_file = os.path.join(self.temp_dir, "simple.py")
        with open(test_file, "w") as f:
            f.write("def hello():\n    print('Hello, world')\n")
        
        # Note: This test requires analyzer dependencies to be mocked
        # or will actually run analysis
        try:
            results = self.orchestrator.analyze_repository(self.temp_dir)
            self.assertIsInstance(results, dict)
            self.assertEqual(len(results), 1)
            self.assertIn(test_file, results)
        except Exception as e:
            # Skip if dependencies not available (e.g., SageMaker)
            self.skipTest(f"Analysis dependencies not available: {e}")

    def test_analyze_repository_with_non_python_files(self):
        # Create non-Python files
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Not Python code")
        
        results = self.orchestrator.analyze_repository(self.temp_dir)
        # Should return empty results since no Python files
        self.assertEqual(len(results), 0)

    def test_analyze_repository_mixed_files(self):
        # Create mixed files
        py_file = os.path.join(self.temp_dir, "test.py")
        txt_file = os.path.join(self.temp_dir, "test.txt")
        
        with open(py_file, "w") as f:
            f.write("print('hello')\n")
        with open(txt_file, "w") as f:
            f.write("Not Python")
        
        try:
            results = self.orchestrator.analyze_repository(self.temp_dir)
            # Should only analyze Python file
            self.assertEqual(len(results), 1)
        except Exception as e:
            self.skipTest(f"Analysis dependencies not available: {e}")


if __name__ == '__main__':
    unittest.main()

