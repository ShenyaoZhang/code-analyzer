import unittest
from code_metrics import CodeMetricsCalculator


class TestCodeMetricsCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = CodeMetricsCalculator()

    def test_count_lines_simple(self):
        code = "def hello():\n    print('hello')\n"
        lines = self.calculator.count_lines(code)
        self.assertEqual(lines, 2)

    def test_count_lines_with_whitespace(self):
        code = "\n\ndef hello():\n    print('hello')\n\n"
        lines = self.calculator.count_lines(code)
        self.assertEqual(lines, 3)

    def test_calculate_complexity_simple(self):
        code = """
def simple():
    return 42
"""
        tree = __import__('ast').parse(code)
        complexity = self.calculator.calculate_complexity(tree)
        self.assertEqual(complexity, 1)  # Base complexity

    def test_calculate_complexity_with_if(self):
        code = """
def with_if(x):
    if x > 0:
        return x
    return 0
"""
        tree = __import__('ast').parse(code)
        complexity = self.calculator.calculate_complexity(tree)
        self.assertEqual(complexity, 2)  # 1 base + 1 if

    def test_calculate_complexity_multiple_statements(self):
        code = """
def complex_func(x):
    if x > 0:
        return x
    for i in range(10):
        if i % 2 == 0:
            print(i)
    while x < 100:
        x += 1
    return x
"""
        tree = __import__('ast').parse(code)
        complexity = self.calculator.calculate_complexity(tree)
        # 1 base + 2 if + 1 for + 1 while = 5
        self.assertEqual(complexity, 5)

    def test_calculate_maintainability_simple(self):
        code = """
def simple():
    return 42
"""
        score = self.calculator.calculate_maintainability(code)
        self.assertGreater(score, 90)  # Simple code should have high score

    def test_calculate_maintainability_complex(self):
        code = """
def complex_func(x):
    for i in range(100):
        for j in range(100):
            if i % 2 == 0:
                if j % 2 == 0:
                    while x < 1000:
                        x += 1
                        if x % 3 == 0:
                            break
    return x
"""
        score = self.calculator.calculate_maintainability(code)
        self.assertLess(score, 50)  # Complex code should have low score

    def test_calculate_maintainability_syntax_error(self):
        code = "def broken(\n"
        score = self.calculator.calculate_maintainability(code)
        self.assertEqual(score, 0.0)  # Syntax errors return 0


if __name__ == '__main__':
    unittest.main()

