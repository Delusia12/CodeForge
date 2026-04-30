"""多 Agent 编排引擎 - 长链推理调度核心"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.text import Text
from rich import box

from src.agents.scanner import ScannerAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.refactor import RefactorAgent
from src.agents.reviewer import ReviewerAgent
from src.tools.code_parser import CodeParser, CodeIssue
from src.tools.diff_gen import DiffGenerator
from src.tools.report import ReportGenerator
from src.config import REPORT_DIR

console = Console()

PHASE_NAMES = [
    ("Scanner", "扫描代码异味"),
    ("Analyzer", "深度分析优先级"),
    ("Refactor", "生成重构方案"),
    ("Reviewer", "审查验证方案"),
]


@dataclass
class PipelineResult:
    target: str
    ast_issues: List[dict] = field(default_factory=list)
    scanner_output: List[dict] = field(default_factory=list)
    analyzer_output: Dict[str, Any] = field(default_factory=dict)
    refactor_suggestions: List[dict] = field(default_factory=list)
    reviewer_output: Dict[str, Any] = field(default_factory=dict)
    report_path: str = ""
    patch_path: str = ""


class Orchestrator:
    """多 Agent 编排器"""

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

    def run(self) -> PipelineResult:
        """执行完整的 4 阶段长链推理流水线"""

        # 流水线图示
        pipeline_viz = (
            "[bold bright_cyan]  Scanner[/]  [dim]→[/]  "
            "[bold cyan]Analyzer[/]  [dim]→[/]  "
            "[bold blue]Refactor[/]  [dim]→[/]  "
            "[bold magenta]Reviewer[/]  [dim]→[/]  "
            "[green]报告[/]"
        )
        console.print(Panel(pipeline_viz, border_style="bright_cyan",
                            title="Pipeline 启动", title_align="left"))
        console.print()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[dim]{task.fields[status]}[/dim]"),
            console=console,
        ) as progress:
            task = progress.add_task("", total=4, status="等待中...")

            # Phase 1
            progress.update(task, description="[cyan]Phase 1/4: Scanner[/cyan]", status="扫描代码库...")
            ast_issues = self._phase_1_scan()
            progress.update(task, advance=1, status=f"发现 {len(ast_issues)} 个问题")

            # Phase 2
            progress.update(task, description="[blue]Phase 2/4: Analyzer[/blue]", status="深度分析中...")
            analysis = self._phase_2_analyze(ast_issues)
            score = analysis.get("overall_score", "?")
            progress.update(task, advance=1, status=f"评分 {score}/100")

            # Phase 3
            progress.update(task, description="[magenta]Phase 3/4: Refactor[/magenta]", status="生成重构方案...")
            refactors = self._phase_3_refactor(ast_issues, analysis)
            progress.update(task, advance=1, status=f"{len(refactors)} 个方案")

            # Phase 4
            progress.update(task, description="[yellow]Phase 4/4: Reviewer[/yellow]", status="审查验证中...")
            review = self._phase_4_review(refactors, ast_issues)
            passed = review.get("passed_count", 0)
            total_r = review.get("total_count", 0)
            progress.update(task, advance=1, status=f"{passed}/{total_r} 通过")

        report_path = self._generate_report(ast_issues, analysis, refactors, review)
        return self.result

    def _phase_1_scan(self) -> list[dict]:
        raw_issues = self.parser.scan_directory(self.target)
        self.result.ast_issues = self.parser.issues_to_dict(raw_issues)
        self._cache_source_snippets(raw_issues)

        if self.use_ai and raw_issues:
            snippets = self._build_snippets(raw_issues)
            ai_issues = self.scanner.scan(self.result.ast_issues, snippets)
            self.result.scanner_output = ai_issues
            return ai_issues

        self.result.scanner_output = self.result.ast_issues
        return self.result.ast_issues

    def _phase_2_analyze(self, issues: list[dict]) -> dict:
        summary = self._build_codebase_summary()
        analysis = self.analyzer.analyze(issues, summary) if self.use_ai else {}
        self.result.analyzer_output = analysis
        return analysis

    def _phase_3_refactor(self, issues: list[dict], analysis: dict) -> list[dict]:
        refactors = self.refactor.generate(issues, analysis, self.source_cache) if self.use_ai else []
        self.result.refactor_suggestions = refactors
        return refactors

    def _phase_4_review(self, refactors: list[dict], issues: list[dict]) -> dict:
        review = self.reviewer.review(refactors, issues) if self.use_ai else {}
        self.result.reviewer_output = review
        return review

    def _generate_report(self, scan, analysis, refactors, review) -> str:
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
            snippets.append({"file": iss.file, "line": iss.line, "type": iss.type, "code": code})
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
        return (f"目标: {self.target}\n"
                f"Python 文件: {len(py_files)}\n"
                f"总行数: {total_lines}\n"
                f"函数/方法: {total_funcs}")
