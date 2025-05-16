class CodeRecommendationEngine:
    def __init__(self):
        # Simple rules mapped by rule codes
        self.recommendation_map = {
            "E501": "Break long lines into shorter ones.",
            "E302": "Add two blank lines before top-level function or class.",
            "missing-docstring": "Add a descriptive docstring to this function or module.",
            "eval-used": "Avoid using eval(); use ast.literal_eval() if possible.",
            "B105": "Avoid hardcoded passwords; use environment variables or secrets manager.",
            "B307": "Replace eval() with ast.literal_eval() or other safe parser.",
            "B605": "Avoid using os.system with shell=True; use subprocess instead.",
            "B607": "Specify full path to the executable in os.system or subprocess.",
        }

    def get_recommendations(self, issues):
        recommendations = []

        for issue in issues:
            rule = issue.get("rule")
            suggestion = self.recommendation_map.get(rule)
            if suggestion:
                recommendations.append({
                    "line": issue.get("line"),
                    "tool": issue.get("tool"),
                    "rule": rule,
                    "suggestion": suggestion,
                    "message": issue.get("message")
                })

        return recommendations
