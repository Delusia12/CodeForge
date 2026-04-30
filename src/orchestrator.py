"""多 Agent 编排引擎 - 长链推理调度核心"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any

from src.agents.scanner import ScannerAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.refactor import RefactorAgent
from src.agents.reviewer import ReviewerAgent
from src.tools.code_parser import CodeParser, CodeIssue
from src.tools.diff_gen import DiffGenerator, RefactorSuggestion
from src.tools.report import ReportGenerator
from src.config import REPORT_DIR


@dataclass
class PipelineResult:
    """长链推理流水线的完整结果"""
    target: str
    ast_issues: List[dict] = field(default_factory=list)
    scanner_output: List[dict] = field(default_factory=list)
    analyzer_output: Dict[str, Any] = field(default_factory=dict)
    refactor_suggestions: List[dict] = field(default_factory=list)
    reviewer_output: Dict[str, Any] = field(default_factory=dict)
    report_path: str = ""
    patch_path: str = ""
    pipeline_log: List[str] = field(default_factory=list)


class Orchestrator:
    """多 Agent 编排器 - 协调 4 个 Agent 完成长链推理"""

    def __init__(self, target: str, use_ai: bool = True):
        self.target = target
        self.use_ai = use_ai
        self.parser = CodeParser()
        self.reporter = ReportGenerator(REPORT_DIR)
        self.diff_gen = DiffGenerator()

        self.scanner = ScannerAgent() if use_ai else None
        self.analyzer = AnalyzerAgent() if use_ai else None
        self.refactor = RefactorAgent() if use_ai else None
        self.reviewer = ReviewerAgent() if use_ai else None

        self.source_cache: dict[str, str] = {}
        self.result = PipelineResult(target=target)

    def log(self, msg: str):
        ts = f"[Orchestrator] {msg}"
        print(f"  {ts}")
        self.result.pipeline_log.append(msg)

    def run(self) -> PipelineResult:
        """执行完整的 4 阶段长链推理流水线"""
        print("\n" + "=" * 60)
        print("  CodeForge - Multi-Agent Code Refactoring Pipeline")
        print("=" * 60 + "\n")

        # Phase 1: AST 扫描
        ast_issues = self._phase_1_scan()
        # Phase 2: AI 深度分析
        analysis = self._phase_2_analyze(ast_issues)
        # Phase 3: 生成重构方案
        refactors = self._phase_3_refactor(ast_issues, analysis)
        # Phase 4: 审查验证
        review = self._phase_4_review(refactors, ast_issues)
        # 生成报告
        report_path = self._generate_report(ast_issues, analysis, refactors, review)

        print("\n" + "=" * 60)
        print("  Pipeline 执行完毕")
        print(f"  报告位置: {report_path}")
        print(f"  发现问题: {len(ast_issues)} → 分析: {analysis.get('overall_score', '?')}分"
              f" → 重构方案: {len(refactors)} → 审查通过: {review.get('passed_count', 0)}/{review.get('total_count', 0)}")
        print("=" * 60 + "\n")

        return self.result

    def _phase_1_scan(self) -> list[dict]:
        """阶段 1: AST 代码扫描"""
        self.log("Phase 1/4: Scanner Agent — 开始扫描代码库...")
        raw_issues = self.parser.scan_directory(self.target)
        self.result.ast_issues = self.parser.issues_to_dict(raw_issues)

        # 缓存源代码片段供后续 Agent 使用
        self._cache_source_snippets(raw_issues)

        self.log(f"  AST 扫描完成，发现 {len(raw_issues)} 个潜在问题")

        if self.use_ai and raw_issues:
            self.log("  AI Scanner 二次确认中...")
            snippets = self._build_snippets(raw_issues)
            ai_issues = self.scanner.scan(self.result.ast_issues, snippets)
            self.result.scanner_output = ai_issues
            self.log(f"  AI 确认: {len(ai_issues)} 个有效问题")
            return ai_issues

        self.result.scanner_output = self.result.ast_issues
        return self.result.ast_issues

    def _phase_2_analyze(self, issues: list[dict]) -> dict:
        """阶段 2: AI 深度分析"""
        self.log("Phase 2/4: Analyzer Agent — 深度分析中...")

        summary = self._build_codebase_summary()
        analysis = self.analyzer.analyze(issues, summary) if self.use_ai else {}
        self.result.analyzer_output = analysis

        score = analysis.get("overall_score", "?")
        self.log(f"  分析完成，代码质量评分: {score}/100")
        self.log(f"  核心关注: {analysis.get('top_concern', 'N/A')}")
        return analysis

    def _phase_3_refactor(self, issues: list[dict], analysis: dict) -> list[dict]:
        """阶段 3: 生成重构方案"""
        self.log("Phase 3/4: Refactor Agent — 生成重构方案...")

        refactors = self.refactor.generate(issues, analysis, self.source_cache) if self.use_ai else []
        self.result.refactor_suggestions = refactors

        self.log(f"  生成 {len(refactors)} 个重构方案")
        return refactors

    def _phase_4_review(self, refactors: list[dict], issues: list[dict]) -> dict:
        """阶段 4: 审查验证"""
        self.log("Phase 4/4: Reviewer Agent — 审查重构方案...")

        review = self.reviewer.review(refactors, issues) if self.use_ai else {}
        self.result.reviewer_output = review

        passed = review.get("passed_count", 0)
        total = review.get("total_count", 0)
        score = review.get("score", "?")
        self.log(f"  审查完成: {passed}/{total} 通过，评分 {score}")
        return review

    def _generate_report(self, scan, analysis, refactors, review) -> str:
        self.log("生成分析报告...")
        path = self.reporter.generate_pipeline_report(scan, analysis, refactors, review)
        self.result.report_path = path
        return path

    def _cache_source_snippets(self, issues: list[CodeIssue]):
        for iss in issues:
            file = iss.file
            if file not in self.source_cache:
                try:
                    self.source_cache[file] = Path(file).read_text(encoding="utf-8")
                except Exception:
                    pass
            key = f"{file}:{iss.line}"
            if key not in self.source_cache:
                cached = self.source_cache.get(file, "")
                lines = cached.split("\n")
                start = max(0, iss.line - 5)
                end = min(len(lines), iss.line + 10)
                self.source_cache[key] = "\n".join(lines[start:end])

    def _build_snippets(self, issues: list[CodeIssue]) -> list[dict]:
        snippets = []
        for iss in issues:
            key = f"{iss.file}:{iss.line}"
            code = self.source_cache.get(key, "")
            snippets.append({
                "file": iss.file, "line": iss.line, "type": iss.type, "code": code
            })
        return snippets

    def _build_codebase_summary(self) -> str:
        path = Path(self.target)
        py_files = list(path.rglob("*.py"))
        total_lines = 0
        total_funcs = 0
        for f in py_files:
            try:
                content = f.read_text(encoding="utf-8")
                total_lines += content.count("\n")
                total_funcs += content.count("def ")
            except Exception:
                pass
        return (f"目标目录: {self.target}\n"
                f"Python 文件数: {len(py_files)}\n"
                f"总代码行数: {total_lines}\n"
                f"函数/方法数: {total_funcs}")
