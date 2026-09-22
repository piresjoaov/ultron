"""Fail-closed presentation boundary for untrusted model text.

This is a formatting and terminal-safety boundary, not a truthfulness verifier.
No raw model output is rendered by the CLI.
"""

import html
import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class OutputReview:
    text: str
    changed: bool
    violations: tuple[str, ...]


class PlainTextOutputPolicy:
    """Canonicalize model output to safe, plain terminal text."""
    _ANSI = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
    _FENCE = re.compile(r"^\s*```[^\n]*$", re.MULTILINE)
    _LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+[^)]*)?\)")
    _HTML_TAG = re.compile(r"</?[^>]+>")
    _HEADING = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
    _BOLD_ITALIC = re.compile(r"(\*\*|__|`)")
    _LIST_STAR = re.compile(r"^\s*\*\s+", re.MULTILINE)

    def review(self, raw_text: str) -> OutputReview:
        violations = []
        text = unicodedata.normalize("NFKC", html.unescape(raw_text or ""))
        if self._ANSI.search(text):
            violations.append("terminal-control-sequence")
            text = self._ANSI.sub("", text)
        if self._FENCE.search(text):
            violations.append("markdown-code-fence")
            text = self._FENCE.sub("", text)
        if self._LINK.search(text):
            violations.append("markdown-link")
            text = self._LINK.sub(r"\1 (\2)", text)
        if self._HTML_TAG.search(text):
            violations.append("html-tag")
            text = self._HTML_TAG.sub("", text)
        if self._HEADING.search(text):
            violations.append("markdown-heading")
            text = self._HEADING.sub("", text)
        if self._BOLD_ITALIC.search(text):
            violations.append("markdown-formatting")
            text = self._BOLD_ITALIC.sub("", text)
        if self._LIST_STAR.search(text):
            violations.append("markdown-list")
            text = self._LIST_STAR.sub("- ", text)
        # Preserve newlines and tabs; remove every other terminal control code.
        text = "".join(char for char in text if char in "\n\t" or ord(char) >= 32)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return OutputReview(text=text, changed=text != raw_text, violations=tuple(dict.fromkeys(violations)))
