import os
import tempfile
import unittest
from pathlib import Path

from tools.filesystem import read_file_text, search_codebase
from tools.registry import TOOLS, TOOL_DEFINITIONS


class FilesystemToolTests(unittest.TestCase):
    def test_read_file_text_supports_inclusive_line_ranges(self):
        with tempfile.TemporaryDirectory() as workspace:
            previous = os.getcwd()
            try:
                os.chdir(workspace)
                Path("sample.py").write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")
                self.assertEqual(read_file_text(path="sample.py", start_line=2, end_line=3), "two\nthree")
            finally:
                os.chdir(previous)

    def test_search_codebase_reports_lines_and_ignores_dependencies(self):
        with tempfile.TemporaryDirectory() as workspace:
            previous = os.getcwd()
            try:
                os.chdir(workspace)
                Path("src").mkdir()
                Path(".venv").mkdir()
                Path("src/app.py").write_text("def target():\n    return True\n", encoding="utf-8")
                Path(".venv/ignored.py").write_text("def target():\n", encoding="utf-8")
                result = search_codebase(r"def\s+target")
                self.assertIn("src/app.py:1: def target():", result)
                self.assertNotIn("ignored.py", result)
            finally:
                os.chdir(previous)

    def test_filesystem_tools_reject_paths_outside_workspace(self):
        with tempfile.TemporaryDirectory() as workspace, tempfile.TemporaryDirectory() as outside:
            previous = os.getcwd()
            try:
                os.chdir(workspace)
                outside_file = Path(outside) / "outside.py"
                outside_file.write_text("secret = True\n", encoding="utf-8")
                self.assertIn("access denied", read_file_text(path=str(outside_file)))
                self.assertIn("access denied", search_codebase("secret", path=str(outside)))
            finally:
                os.chdir(previous)

    def test_search_codebase_is_registered_with_guidance(self):
        self.assertIs(TOOLS["search_codebase"], search_codebase)
        definition = next(item for item in TOOL_DEFINITIONS if item["function"]["name"] == "search_codebase")
        self.assertIn("function definition", definition["function"]["description"])
        self.assertEqual(definition["function"]["parameters"]["required"], ["query"])


if __name__ == "__main__":
    unittest.main()
