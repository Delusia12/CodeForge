"""AST 代码解析器 - 检测技术债和代码异味"""

import ast
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class CodeIssue:
    file: str
    line: int
    type: str
    severity: str  # high / medium / low
    description: str
    suggestion: str = ""


class CodeParser:
    def __init__(self, thresholds: dict | None = None):
        from src.config import CODE_SMELL_THRESHOLDS
        self.thresholds = thresholds or CODE_SMELL_THRESHOLDS

    def scan_directory(self, path: str) -> list[CodeIssue]:
        issues = []
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(".py"):
                    filepath = os.path.join(root, f)
                    issues.extend(self.scan_file(filepath))
        return issues

    def scan_file(self, filepath: str) -> list[CodeIssue]:
        with open(filepath, "r", encoding="utf-8") as fh:
            source = fh.read()
        lines = source.split("\n")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        issues = []
        issues.extend(self._check_long_functions(tree, filepath, lines))
        issues.extend(self._check_complex_conditionals(tree, filepath, lines))
        issues.extend(self._check_too_many_params(tree, filepath, lines))
        issues.extend(self._check_deep_nesting(tree, filepath, lines))
        issues.extend(self._check_duplicate_code(tree, filepath, lines))
        issues.extend(self._check_bare_except(tree, filepath, lines))
        issues.extend(self._check_todo_fixme(filepath, lines))
        return issues

    def _get_line(self, node: ast.AST) -> int:
        return getattr(node, "lineno", 1)

    def _count_lines(self, node: ast.AST) -> int:
        end = getattr(node, "end_lineno", None)
        if end:
            return max(0, end - self._get_line(node))
        return 0

    def _check_long_functions(self, tree, filepath, lines) -> list[CodeIssue]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = self._count_lines(node)
                limit = self.thresholds["max_function_lines"]
                if length > limit:
                    issues.append(CodeIssue(
                        file=filepath, line=self._get_line(node),
                        type="long_function", severity="high",
                        description=f"函数 '{node.name}' 过长 ({length} 行, 阈值 {limit})",
                        suggestion=f"建议拆分为多个小函数，每个负责单一职责"
                    ))
        return issues

    def _check_complex_conditionals(self, tree, filepath, lines) -> list[CodeIssue]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._cyclomatic_complexity(node)
                limit = self.thresholds["max_cyclomatic_complexity"]
                if complexity > limit:
                    issues.append(CodeIssue(
                        file=filepath, line=self._get_line(node),
                        type="high_complexity", severity="high",
                        description=f"函数 '{node.name}' 圈复杂度 {complexity} (阈值 {limit})",
                        suggestion="考虑提取条件分支为独立函数，或使用策略模式"
                    ))
        return issues

    def _cyclomatic_complexity(self, node: ast.AST) -> int:
        count = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While,
                                   ast.And, ast.Or, ast.ExceptHandler,
                                   ast.Try, ast.With, ast.AsyncWith)):
                count += 1
            elif isinstance(child, ast.BoolOp):
                count += len(child.values) - 1
        return count

    def _check_too_many_params(self, tree, filepath, lines) -> list[CodeIssue]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = [a for a in node.args.args if a.arg != "self"]
                limit = self.thresholds["max_parameters"]
                if len(params) > limit:
                    issues.append(CodeIssue(
                        file=filepath, line=self._get_line(node),
                        type="too_many_params", severity="medium",
                        description=f"函数 '{node.name}' 参数过多 ({len(params)} 个, 阈值 {limit})",
                        suggestion="考虑用 dataclass 或 TypedDict 封装相关参数"
                    ))
        return issues

    def _check_deep_nesting(self, tree, filepath, lines) -> list[CodeIssue]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                depth = self._max_nesting(node)
                limit = self.thresholds["max_nesting_depth"]
                if depth > limit:
                    issues.append(CodeIssue(
                        file=filepath, line=self._get_line(node),
                        type="deep_nesting", severity="medium",
                        description=f"函数 '{node.name}' 嵌套深度 {depth} (阈值 {limit})",
                        suggestion="用提前返回 (guard clause) 减少嵌套"
                    ))
        return issues

    def _max_nesting(self, node: ast.AST, current: int = 0) -> int:
        if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            current += 1
        child_depths = [self._max_nesting(c, current) for c in ast.iter_child_nodes(node)]
        return max([current] + child_depths + [0])

    def _check_duplicate_code(self, tree, filepath, lines) -> list[CodeIssue]:
        """检测疑似重复代码块 (简化版: 检测相同长度的 if 链)"""
        issues = []
        blocks: dict[int, list[str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.If):
                        block_lines = self._count_lines(child)
                        name = getattr(child.test, "id", None) or str(type(child.test).__name__)
                        key = block_lines
                        if key not in blocks:
                            blocks[key] = []
                        blocks[key].append(name)
        for count, names in blocks.items():
            if len(names) >= 3 and count > 3:
                issues.append(CodeIssue(
                    file=filepath, line=self._get_line(node) if 'node' in dir() else 1,
                    type="duplicate_pattern", severity="low",
                    description=f"检测到 {len(names)} 个相似的 if 代码块 (各 {count} 行)",
                    suggestion="考虑提取公共逻辑为函数"
                ))
        return issues

    def _check_bare_except(self, tree, filepath, lines) -> list[CodeIssue]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append(CodeIssue(
                        file=filepath, line=self._get_line(node),
                        type="bare_except", severity="medium",
                        description="使用了裸 except: 可能隐藏关键错误",
                        suggestion="指定具体的异常类型，如 except ValueError"
                    ))
        return issues

    def _check_todo_fixme(self, filepath, lines) -> list[CodeIssue]:
        issues = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") and ("TODO" in stripped or "FIXME" in stripped):
                issues.append(CodeIssue(
                    file=filepath, line=i,
                    type="todo_fixme", severity="low",
                    description=f"遗留标记: {stripped.lstrip('#').strip()}",
                    suggestion="完成或移除该标记"
                ))
        return issues

    def issues_to_dict(self, issues: list[CodeIssue]) -> list[dict]:
        return [asdict(iss) for iss in issues]
