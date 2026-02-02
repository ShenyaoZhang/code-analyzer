import unittest
from duplication_detector import DuplicationDetector


class TestDuplicationDetector(unittest.TestCase):
    def setUp(self):
        self.detector = DuplicationDetector(min_lines=3)

    def test_no_duplicates(self):
        file_map = {
            "file1.py": "def func1():\n    print('hello')\n",
            "file2.py": "def func2():\n    print('world')\n"
        }
        duplicates = self.detector.find_duplicates(file_map)
        self.assertEqual(len(duplicates), 0)

    def test_find_exact_duplicates(self):
        code_snippet = "    name = input('Name? ')\n    print('Hello', name)\n    print('Welcome!')"
        file_map = {
            "file1.py": f"def greet():\n{code_snippet}\n",
            "file2.py": f"def say_hi():\n{code_snippet}\n"
        }
        duplicates = self.detector.find_duplicates(file_map)
        self.assertGreater(len(duplicates), 0)
        
        # Check that duplicate info is correct
        dup = duplicates[0]
        self.assertIn('duplicate_in', dup)
        self.assertIn('original_in', dup)
        self.assertIn('line_range', dup)
        self.assertIn('snippet', dup)

    def test_min_lines_threshold(self):
        # 2-line snippet should not be detected with min_lines=3
        detector_3 = DuplicationDetector(min_lines=3)
        file_map = {
            "file1.py": "x = 1\ny = 2\n",
            "file2.py": "x = 1\ny = 2\n"
        }
        duplicates = detector_3.find_duplicates(file_map)
        self.assertEqual(len(duplicates), 0)
        
        # Should be detected with min_lines=2
        detector_2 = DuplicationDetector(min_lines=2)
        duplicates = detector_2.find_duplicates(file_map)
        self.assertGreater(len(duplicates), 0)

    def test_hash_snippet_consistency(self):
        lines1 = ["def foo():", "    pass"]
        lines2 = ["def foo():", "    pass"]
        
        hash1 = self.detector.hash_snippet(lines1)
        hash2 = self.detector.hash_snippet(lines2)
        
        self.assertEqual(hash1, hash2)

    def test_hash_snippet_different(self):
        lines1 = ["def foo():", "    pass"]
        lines2 = ["def bar():", "    pass"]
        
        hash1 = self.detector.hash_snippet(lines1)
        hash2 = self.detector.hash_snippet(lines2)
        
        self.assertNotEqual(hash1, hash2)

    def test_multiple_duplicates(self):
        common = "x = 1\ny = 2\nz = 3\n"
        file_map = {
            "file1.py": common + "a = 4\n",
            "file2.py": common + "b = 5\n",
            "file3.py": common + "c = 6\n"
        }
        duplicates = self.detector.find_duplicates(file_map)
        # Each file after the first should have duplicates detected
        self.assertGreaterEqual(len(duplicates), 2)

    def test_empty_files(self):
        file_map = {
            "file1.py": "",
            "file2.py": ""
        }
        duplicates = self.detector.find_duplicates(file_map)
        self.assertEqual(len(duplicates), 0)


if __name__ == '__main__':
    unittest.main()

