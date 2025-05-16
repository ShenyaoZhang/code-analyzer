import ast

class CodeMetricsCalculator:
    def __init__(self):
        pass

    def calculate_complexity(self, tree):
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                complexity += 1
        return complexity + 1  # +1 for the entry point

    def count_lines(self, code):
        return len(code.strip().splitlines())

    def calculate_maintainability(self, code):
        try:
            tree = ast.parse(code)
            loc = self.count_lines(code)
            complexity = self.calculate_complexity(tree)

            # Simplified maintainability index formula (mock version)
            score = max(0, 100 - (complexity * 2 + loc * 0.5))
            return round(score, 2)
        except SyntaxError:
            return 0.0
