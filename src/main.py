#!/usr/bin/env python3
"""CodeForge — 多 Agent 协作代码审查&重构流水线

用法:
    python -m src.main --target <代码目录>
    python -m src.main --target examples/sample_code/ --no-ai
    python -m src.main --target . --output reports/my_report.md
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.orchestrator import Orchestrator
from src.config import REPORT_DIR


def main():
    parser = argparse.ArgumentParser(
        description="CodeForge - Multi-Agent Code Refactoring Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m src.main --target examples/sample_code/
  python -m src.main --target examples/sample_code/ --no-ai   # 仅 AST 扫描模式
  python -m src.main --target ./src/ --output my_report.md
        """
    )
    parser.add_argument("--target", "-t", required=True,
                        help="要扫描的目标代码目录")
    parser.add_argument("--no-ai", action="store_true",
                        help="仅使用 AST 扫描，跳过 AI Agent 分析")
    parser.add_argument("--output", "-o", default=None,
                        help="报告输出文件路径 (默认: reports/codeforge_report_<timestamp>.md)")

    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"错误: 目标路径不存在: {target}")
        sys.exit(1)

    use_ai = not args.no_ai
    if use_ai:
        from src.config import ANTHROPIC_API_KEY, OPENAI_API_KEY
        if not ANTHROPIC_API_KEY and not OPENAI_API_KEY:
            print("警告: 未检测到 AI API Key，将仅使用 AST 扫描模式")
            print("请设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 环境变量，或复制 .env.example 为 .env 并填入 Key")
            use_ai = False

    print(f"\n目标目录: {target}")
    print(f"AI 模式: {'启用 (多 Agent 协作)' if use_ai else '禁用 (仅 AST 扫描)'}")
    print(f"报告目录: {REPORT_DIR}\n")

    orch = Orchestrator(str(target), use_ai=use_ai)
    result = orch.run()

    if result.report_path:
        print(f"\n报告已生成: {result.report_path}")

    # 打印摘要
    print("\n--- 执行摘要 ---")
    for entry in result.pipeline_log:
        print(f"  {entry}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
