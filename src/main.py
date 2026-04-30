#!/usr/bin/env python3
"""CodeForge — 多 Agent 协作代码审查&重构流水线"""

import argparse
import sys
import os
from pathlib import Path

# Windows 终端强制 UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from src.orchestrator import Orchestrator
from src.tools.code_parser import CodeParser
from src.tools.report import ReportGenerator
from src.config import REPORT_DIR

console = Console(force_terminal=True)


def banner():
    title = Text()
    title.append("> ", style="bold bright_cyan")
    title.append("CodeForge", style="bold white")
    title.append("  Multi-Agent Code Refactoring Pipeline", style="dim")
    console.print(Panel(title, box=box.HEAVY, border_style="bright_cyan"))
    console.print("  Scanner -> Analyzer -> Refactor -> Reviewer  [Long-chain Reasoning]\n",
                  style="dim italic")


def show_ast_results(issues: list, report_path: str):
    sev_style = {"high": "bold red", "medium": "bold yellow", "low": "dim green"}
    sev_mark = {"high": "[HIGH]", "medium": "[MED]", "low": "[LOW]"}

    console.print()

    groups: dict[str, list] = {}
    for iss in issues:
        sev = iss.get("severity", "low") if isinstance(iss, dict) else getattr(iss, "severity", "low")
        groups.setdefault(sev, []).append(iss)

    total = len(issues)
    high = len(groups.get("high", []))
    medium = len(groups.get("medium", []))
    low = len(groups.get("low", []))

    summary = Text()
    summary.append("Scan Complete  |  ", style="dim")
    summary.append(f"{total} issues found  ", style="bold white")
    if high:
        summary.append(f"  [HIGH] x{high}", style="bold red")
    if medium:
        summary.append(f"  [MED] x{medium}", style="bold yellow")
    if low:
        summary.append(f"  [LOW] x{low}", style="green")
    console.print(Panel(summary, border_style="cyan", title="Scanner Agent Result",
                        title_align="left"))

    for sev in ("high", "medium", "low"):
        items = groups.get(sev, [])
        if not items:
            continue

        table = Table(
            title=f"{sev_mark[sev]} {sev.upper()} — {len(items)} items",
            title_style=sev_style.get(sev, ""),
            box=box.SIMPLE_HEAVY,
            border_style="dim",
            show_lines=False,
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("File", style="cyan", max_width=40)
        table.add_column("Line", style="dim", width=5)
        table.add_column("Type", style="yellow", max_width=20)
        table.add_column("Description", style="white")

        for i, iss in enumerate(items, 1):
            f = iss.get("file") if isinstance(iss, dict) else getattr(iss, "file", "")
            l = iss.get("line", 0) if isinstance(iss, dict) else getattr(iss, "line", 0)
            t = iss.get("type", "") if isinstance(iss, dict) else getattr(iss, "type", "")
            d = iss.get("description", "") if isinstance(iss, dict) else getattr(iss, "description", "")
            f_short = f.replace("\\", "/").split("/")[-1] if f else ""
            table.add_row(str(i), f_short, str(l), t, d)

        console.print(table)

    console.print()

    tips_text = "\n".join([
        ">> Configure AI API Key to enable Multi-Agent deep analysis:",
        "   cp .env.example .env  ->  add ANTHROPIC_API_KEY or OPENAI_API_KEY",
        "   python -m src.main --target <dir>",
    ])
    console.print(Panel(tips_text, title="Next Step", title_align="left",
                        border_style="green"))

    console.print(f"[dim]Report saved: {report_path}[/dim]\n")


def show_ai_pipeline_result(result, report_path: str):
    console.print()
    analysis = result.analyzer_output
    review = result.reviewer_output

    table = Table(title="Pipeline Result", box=box.ROUNDED, border_style="bright_cyan")
    table.add_column("Phase", style="bold cyan")
    table.add_column("Agent", style="yellow")
    table.add_column("Result", style="white")

    table.add_row("Phase 1", "Scanner", f"Found {len(result.scanner_output)} issues")
    score = analysis.get("overall_score", "?")
    table.add_row("Phase 2", "Analyzer",
                  f"Quality Score {score}/100  |  Top Concern: {analysis.get('top_concern', 'N/A')}")
    table.add_row("Phase 3", "Refactor",
                  f"Generated {len(result.refactor_suggestions)} refactoring plans")
    passed = review.get("passed_count", 0)
    total_r = review.get("total_count", 0)
    table.add_row("Phase 4", "Reviewer",
                  f"Review {passed}/{total_r} passed  |  Grade {review.get('score', '?')}")

    console.print(table)
    console.print(f"\n[dim]Report saved: {report_path}[/dim]\n")


def main():
    parser = argparse.ArgumentParser(description="CodeForge - Multi-Agent Code Refactoring Pipeline")
    parser.add_argument("--target", "-t", required=True, help="Target code directory")
    parser.add_argument("--no-ai", action="store_true", help="AST-only scan, skip AI Agents")
    parser.add_argument("--output", "-o", default=None, help="Report output path")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        console.print(f"[red]Error: target not found: {target}[/red]")
        sys.exit(1)

    use_ai = not args.no_ai
    if use_ai:
        from src.config import ANTHROPIC_API_KEY, OPENAI_API_KEY
        if not ANTHROPIC_API_KEY and not OPENAI_API_KEY:
            console.print("[yellow]No AI API Key found, falling back to AST-only mode[/yellow]")
            console.print("[dim]Set ANTHROPIC_API_KEY or OPENAI_API_KEY to enable Multi-Agent mode[/dim]")
            use_ai = False

    banner()

    if use_ai:
        orch = Orchestrator(str(target), use_ai=True)
        result = orch.run()
        show_ai_pipeline_result(result, result.report_path)
    else:
        parser_obj = CodeParser()
        issues = parser_obj.scan_directory(str(target))
        issues_dict = parser_obj.issues_to_dict(issues)
        reporter = ReportGenerator(REPORT_DIR)
        report_path = reporter.generate_pipeline_report(
            scan_issues=issues_dict,
            analysis_result={"summary": "(AI analysis not enabled)", "high_count": 0,
                             "medium_count": 0, "low_count": 0, "overall_score": 0,
                             "top_concern": "N/A", "details": [], "refactor_priority": []},
            refactor_suggestions=[],
            review_result={"passed_count": 0, "total_count": 0, "score": "N/A",
                           "verdict": "Configure AI API Key to enable full analysis"}
        )
        show_ast_results(issues_dict, report_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
