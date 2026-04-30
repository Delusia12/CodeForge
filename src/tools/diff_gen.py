"""Diff 生成器 - 将重构方案转为 unified diff 格式"""

from dataclasses import dataclass
from typing import List


@dataclass
class RefactorSuggestion:
    file: str
    original_lines: str
    new_lines: str
    start_line: int
    end_line: int
    reason: str
    confidence: float  # 0-1


class DiffGenerator:

    @staticmethod
    def generate(suggestions: list[RefactorSuggestion]) -> str:
        parts = []
        for s in suggestions:
            parts.append(DiffGenerator._single_diff(s))
        return "\n".join(parts)

    @staticmethod
    def _single_diff(s: RefactorSuggestion) -> str:
        """生成单个文件的 unified diff"""
        header = f"--- a/{s.file}\n+++ b/{s.file}\n"
        original = s.original_lines.rstrip("\n")
        new = s.new_lines.rstrip("\n")
        orig_lines = original.split("\n")
        new_lines = new.split("\n")
        hunk = f"@@ -{s.start_line},{len(orig_lines)} +{s.start_line},{len(new_lines)} @@"
        body_lines = []
        for ol in orig_lines:
            body_lines.append(f"-{ol}")
        for nl in new_lines:
            body_lines.append(f"+{nl}")
        body = "\n".join(body_lines)
        meta = (f"# 原因: {s.reason}\n"
                f"# 置信度: {s.confidence:.0%}\n"
                f"# 位置: {s.file}:{s.start_line}-{s.end_line}")
        return f"{meta}\n{header}{hunk}\n{body}\n"

    @staticmethod
    def generate_patch_file(suggestions: list[RefactorSuggestion], output_path: str):
        diff_text = DiffGenerator.generate(suggestions)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(diff_text)
        return output_path
