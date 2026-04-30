"""Analyzer Agent - 深度分析引擎"""

from src.agents.base import BaseAgent


class AnalyzerAgent(BaseAgent):
    name = "analyzer"
    description = "深度分析代码问题，评估严重性和影响范围，给出优先级排序"

    def system_prompt(self) -> str:
        return """你是一名资深软件架构师，负责分析代码质量问题的严重性和优先级。

你的输出必须是纯 JSON 对象，格式：
{
  "summary": "一段中文概述，说明主要发现了什么问题",
  "high_count": 3,
  "medium_count": 5,
  "low_count": 2,
  "overall_score": 72,
  "top_concern": "当前最大的架构风险是什么",
  "details": [
    "高优先级问题1的描述和影响分析",
    "高优先级问题2的描述和影响分析"
  ],
  "refactor_priority": ["问题1的file:line", "问题2的file:line"]
}

评分规则：
- overall_score: 0-100 代码质量评分，越高越好
- 如果高优先级问题超过 5 个，重点分析 5 个最关键的问题"""

    def analyze(self, scanner_output: list[dict], codebase_summary: str) -> dict:
        """对 Scanner 输出进行深度分析和优先级排序"""
        if not scanner_output:
            return {
                "summary": "未发现显著的代码质量问题。",
                "high_count": 0, "medium_count": 0, "low_count": 0,
                "overall_score": 95,
                "top_concern": "无明显架构风险",
                "details": [],
                "refactor_priority": []
            }

        issues_text = "\n".join(
            f"{i+1}. [{iss.get('severity', '?')}] {iss.get('file', '?')}:{iss.get('line', '?')}"
            f" — {iss.get('type', '?')}: {iss.get('description', '')}"
            for i, iss in enumerate(scanner_output[:30])
        )

        prompt = f"""请分析以下代码扫描结果并进行优先级排序：

## 代码库概况
{codebase_summary}

## 发现问题（共 {len(scanner_output)} 项）
{issues_text}

请按照系统提示词的 JSON 格式输出分析结果。重点：
1. 区分哪些问题是真正的技术债，哪些可以忽略
2. 按严重性和修复难度交叉排序
3. 给出具体的修复优先级顺序"""

        try:
            return self.ask_json(prompt)
        except Exception as e:
            return {
                "summary": f"AI 分析出错: {e}",
                "high_count": sum(1 for i in scanner_output if i.get("severity") == "high"),
                "medium_count": sum(1 for i in scanner_output if i.get("severity") == "medium"),
                "low_count": sum(1 for i in scanner_output if i.get("severity") == "low"),
                "overall_score": 60,
                "top_concern": "分析过程异常",
                "details": [],
                "refactor_priority": []
            }
