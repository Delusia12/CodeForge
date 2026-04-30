"""报告生成器 - 输出 Markdown / HTML 报告"""

import json
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
from typing import List


class ReportGenerator:

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_pipeline_report(
        self,
        scan_issues: list,
        analysis_result: dict,
        refactor_suggestions: list,
        review_result: dict,
    ) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"codeforge_report_{timestamp}.md"
        filepath = self.output_dir / filename

        md = self._build_markdown(
            scan_issues, analysis_result, refactor_suggestions, review_result
        )

        filepath.write_text(md, encoding="utf-8")
        return str(filepath)

    def _build_markdown(self, scan, analysis, refactors, review) -> str:
        lines = []
        lines.append(f"# CodeForge 多 Agent 重构分析报告")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Pipeline 概览
        lines.append("## Pipeline 概览")
        lines.append("")
        lines.append("```")
        lines.append("Scanner → Analyzer → Refactor → Reviewer")
        lines.append("   ↓          ↓           ↓           ↓")
        lines.append(" 代码扫描   深度分析    重构方案    审查验证")
        lines.append("```")
        lines.append("")

        # Scanner 输出
        lines.append("## Phase 1: Scanner Agent — 代码异味扫描")
        lines.append(f"共发现 **{len(scan)}** 个潜在问题")
        lines.append("")
        by_severity = {"high": [], "medium": [], "low": []}
        for iss in scan:
            sev = iss.get("severity", iss.severity if hasattr(iss, "severity") else "low")
            by_severity.setdefault(sev, []).append(iss)
        for sev in ("high", "medium", "low"):
            items = by_severity.get(sev, [])
            icon = {"high": "[HIGH]", "medium": "[MED]", "low": "[LOW]"}.get(sev, "")
            lines.append(f"### {icon} {sev.upper()} 严重度 — {len(items)} 项")
            for item in items:
                if hasattr(item, "file"):
                    d = item.description
                    f = item.file
                    l = item.line
                else:
                    d = item.get("description", "")
                    f = item.get("file", "")
                    l = item.get("line", 0)
                t = item.get("type", "") if isinstance(item, dict) else getattr(item, "type", "")
                lines.append(f"- **`{f}:{l}`** [{t}] — {d}")
            lines.append("")

        # Analyzer 输出
        lines.append("## Phase 2: Analyzer Agent — 深度分析")
        if isinstance(analysis, dict):
            lines.append(f"- 优先级排序完成，高优先级 {analysis.get('high_count', 0)} 项")
            lines.append(f"- 分析摘要: {analysis.get('summary', 'N/A')}")
            details = analysis.get("details", [])
            for d in details:
                lines.append(f"  - {d}")
        lines.append("")

        # Refactor 输出
        lines.append("## Phase 3: Refactor Agent — 重构方案")
        lines.append(f"共生成 **{len(refactors)}** 个重构方案")
        for i, r in enumerate(refactors, 1):
            if hasattr(r, "reason"):
                reason, conf, file, sline, eline = r.reason, r.confidence, r.file, r.start_line, r.end_line
            else:
                reason = r.get("reason", "")
                conf = r.get("confidence", 0)
                file = r.get("file", "")
                sline = r.get("start_line", 0)
                eline = r.get("end_line", 0)
            lines.append(f"### 方案 {i}: `{file}:{sline}-{eline}`")
            lines.append(f"- **置信度**: {conf:.0%}" if isinstance(conf, float) else f"- **置信度**: {conf}")
            lines.append(f"- **理由**: {reason}")
            lines.append("")
            lines.append("```diff")
            if hasattr(r, "original_lines"):
                lines.append(r.original_lines[:300])
            else:
                lines.append(r.get("original_lines", "")[:300])
            lines.append("```")
            lines.append("")

        # Reviewer 输出
        lines.append("## Phase 4: Reviewer Agent — 审查验证")
        passed = review.get("passed_count", 0) if isinstance(review, dict) else 0
        total = review.get("total_count", 0) if isinstance(review, dict) else 0
        lines.append(f"审查结果: **{passed}/{total}** 通过")
        lines.append(f"总体评分: **{review.get('score', 'N/A') if isinstance(review, dict) else 'N/A'}**")
        verdict = review.get("verdict", "") if isinstance(review, dict) else ""
        if verdict:
            lines.append(f"结论: {verdict}")
        lines.append("")

        lines.append("---")
        lines.append("\n*由 CodeForge 多 Agent 协作流水线自动生成*")
        return "\n".join(lines)
