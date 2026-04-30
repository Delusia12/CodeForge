"""Refactor Agent - 重构方案生成器"""

from src.agents.base import BaseAgent


class RefactorAgent(BaseAgent):
    name = "refactor"
    description = "根据分析结果生成具体的代码重构方案"

    def system_prompt(self) -> str:
        return """你是一名资深代码重构专家。根据分析结果，生成具体的重构方案。

输出纯 JSON 数组：
[
  {
    "file": "文件路径",
    "start_line": 起始行号,
    "end_line": 结束行号,
    "reason": "重构理由（中文）",
    "confidence": 0.85,
    "original_lines": "原始代码（关键片段）",
    "new_lines": "重构后代码"
  }
]

要求：
- confidence 0-1 表示你对这个重构方案的信心
- 每次只对最高优先级的 3 个问题进行重构
- 重构后的代码必须保持语义一致
- 优先使用 Python 最佳实践（类型标注、dataclass、context manager 等）"""

    def generate(self, issues: list[dict], analysis: dict, source_cache: dict) -> list[dict]:
        """为高优先级问题生成重构方案"""
        priority = analysis.get("refactor_priority", [])
        if not priority:
            return []

        top_issues = []
        for p in priority[:3]:
            for iss in issues:
                key = f"{iss.get('file', '')}:{iss.get('line', '')}"
                if key == p:
                    top_issues.append(iss)
                    break

        if not top_issues:
            # fallback: 选前 3 个高严重性问题
            top_issues = [i for i in issues if i.get("severity") == "high"][:3]
        if not top_issues:
            top_issues = issues[:3]

        context_parts = []
        for iss in top_issues:
            file = iss.get("file", "")
            code = source_cache.get(f"{file}:{iss.get('line', 0)}",
                                     source_cache.get(file, ""))
            context_parts.append(
                f"### {file}:{iss.get('line', '?')}\n"
                f"问题类型: {iss.get('type', '?')}\n"
                f"严重程度: {iss.get('severity', '?')}\n"
                f"描述: {iss.get('description', '')}\n"
                f"```python\n{code[:500]}\n```"
            )

        prompt = "请为以下问题生成具体的重构方案：\n\n" + "\n\n".join(context_parts)

        try:
            return self.ask_json(prompt)
        except Exception:
            return []
