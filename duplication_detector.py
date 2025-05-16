import hashlib

class DuplicationDetector:
    def __init__(self, min_lines=3):
        self.min_lines = min_lines  # minimum number of lines to consider duplication

    def hash_snippet(self, lines):
        snippet = "\n".join(lines).strip()
        return hashlib.md5(snippet.encode("utf-8")).hexdigest()

    def find_duplicates(self, file_map):
        """
        file_map: dict of {file_path: file_content_str}
        Returns: list of dicts with duplicate info
        """
        seen = {}
        duplicates = []

        for file_path, code in file_map.items():
            lines = code.splitlines()
            for i in range(len(lines) - self.min_lines + 1):
                snippet_lines = lines[i:i + self.min_lines]
                snippet_hash = self.hash_snippet(snippet_lines)

                if snippet_hash in seen:
                    duplicates.append({
                        "duplicate_in": file_path,
                        "original_in": seen[snippet_hash]["file"],
                        "line_range": [i + 1, i + self.min_lines],
                        "snippet": "\n".join(snippet_lines)
                    })
                else:
                    seen[snippet_hash] = {"file": file_path, "start": i + 1}

        return duplicates
