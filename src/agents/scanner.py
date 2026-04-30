"""Scanner Agent - 代码异味扫描器"""

from src.agents.base import BaseAgent


class ScannerAgent(BaseAgent):
    name = "scanner"
    description = "扫描代码仓库，检测代码异味和技术债"

    def system_prompt(self) -> str:
        return """你是一个资深代码审查专家，负责扫描代码中的技术债和代码异味。

你的输出必须是纯 JSON 数组，不要包含任何其他文字。格式：
[{"file": "path/to/file.py", "line": 42, "type": "long_function", "severity": "high", "description": "..."}]

severity 必须是 high / medium / low 之一。
type 可以是: long_function, high_complexity, too_many_params, deep_nesting, duplicate_code, bare_except, todo_fixme, magic_number, unclear_name

请给出具体、可操作的描述，使用中文。"""

    def scan(self, ast_issues: list[dict], source_snippets: list[dict]) -> list[dict]:
        """结合 AST 分析结果，用 LLM 进行二次确认和补充"""
        if not source_snippets:
            return ast_issues

        snippet_text = "\n---\n".join(
            f"[{s['file']}:{s.get('line', '?')}] {s.get('type', 'unknown')}\n```\n{s.get('code', '')}\n```"
            for s in source_snippets[:15]
        )

        prompt = f"""以下 AST 初步扫描发现了这些潜在问题：

{self._format_ast_issues(ast_issues)}

以下是问题代码片段，请审查并：
1. 确认 AST 发现的问题是否真实
2. 补充 AST 可能遗漏的语义问题（如命名不清晰、逻辑疑似错误）

{snippet_text}

返回 JSON 数组，包含确认+新增的所有问题。"""

        try:
            return self.ask_json(prompt)
        except Exception:
            return ast_issues

    def _format_ast_issues(self, issues: list[dict]) -> str:
        lines = []
        for iss in issues[:20]:
            lines.append(f"- [{iss.get('severity', '?')}] {iss.get('file', '?')}:{iss.get('line', '?')}"
                         f" — {iss.get('type', '?')}: {iss.get('description', '')}")
        return "\n".join(lines) if lines else "（无 AST 发现的问题）"
