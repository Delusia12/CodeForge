"""Reviewer Agent - 审查验证器"""

from src.agents.base import BaseAgent


class ReviewerAgent(BaseAgent):
    name = "reviewer"
    description = "审查重构方案的合理性，验证语义一致性，输出最终决策"

    def system_prompt(self) -> str:
        return """你是一名严谨的代码审查员，负责审查重构方案。

输出纯 JSON：
{
  "passed_count": 2,
  "total_count": 3,
  "score": "A",
  "verdict": "通过。建议直接应用重构方案1和2，方案3需微调后应用。",
  "details": [
    {
      "id": 1,
      "passed": true,
      "comment": "拆分合理，单一职责明确"
    },
    {
      "id": 2,
      "passed": true,
      "comment": "引入 dataclass 减少了参数传递的复杂度"
    },
    {
      "id": 3,
      "passed": false,
      "comment": "提取函数后丢失了异常处理语义",
      "fix_suggestion": "在提取后的函数内部保留 try/except"
    }
  ],
  "test_suggestions": [
    "为重构后的函数 _validate_input 添加参数化测试",
    "验证空列表边界情况"
  ]
}

评分等级: A (优秀) / B (良好) / C (需修改) / D (不建议合并)

审查重点：
1. 重构后语义是否完全一致
2. 是否引入了新 bug
3. 边界条件是否处理正确
4. 错误处理是否保留"""

    def review(self, refactor_suggestions: list[dict], original_issues: list[dict]) -> dict:
        """审查所有重构方案"""
        if not refactor_suggestions:
            return {
                "passed_count": 0, "total_count": 0,
                "score": "N/A",
                "verdict": "无重构方案可审查",
                "details": [],
                "test_suggestions": []
            }

        suggestion_text = "\n---\n".join(
            f"方案 {i+1}:\n"
            f"文件: {s.get('file', '?')}:{s.get('start_line', '?')}-{s.get('end_line', '?')}\n"
            f"理由: {s.get('reason', '?')}\n"
            f"原始:\n```\n{s.get('original_lines', '')[:400]}\n```\n"
            f"重构后:\n```\n{s.get('new_lines', '')[:400]}\n```"
            for i, s in enumerate(refactor_suggestions)
        )

        issues_context = "\n".join(
            f"- [{i.get('severity', '?')}] {i.get('file', '?')}:{i.get('line', '?')} — {i.get('description', '')}"
            for i in original_issues[:10]
        )

        prompt = f"""请审查以下 {len(refactor_suggestions)} 个重构方案：

## 原始问题
{issues_context}

## 重构方案
{suggestion_text}

请逐一审查，给出通过/不通过的判断和详细意见。"""

        try:
            return self.ask_json(prompt)
        except Exception as e:
            return {
                "passed_count": 0, "total_count": len(refactor_suggestions),
                "score": "N/A",
                "verdict": f"审查过程异常: {e}",
                "details": [],
                "test_suggestions": []
            }
