"""CodeForge Pipeline 集成测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tools.code_parser import CodeParser
from src.tools.diff_gen import DiffGenerator, RefactorSuggestion
from src.tools.report import ReportGenerator
from src.config import REPORT_DIR


class TestCodeParser:
    def test_scan_file(self):
        parser = CodeParser()
        fixture = Path(__file__).parent / "fixtures" / "bad_code.py"
        issues = parser.scan_file(str(fixture))
        assert len(issues) > 0, "应该检测出至少一个问题"
        types = {iss.type for iss in issues}
        assert "deep_nesting" in types, "应该检测出过深嵌套"
        assert "bare_except" in types, "应该检测出裸 except"

    def test_scan_directory(self):
        parser = CodeParser()
        sample_dir = Path(__file__).parent.parent / "examples" / "sample_code"
        issues = parser.scan_directory(str(sample_dir))
        assert len(issues) > 0, "sample_code 目录应该有可检测的问题"

    def test_long_function_detection(self):
        parser = CodeParser()
        fixture = Path(__file__).parent / "fixtures" / "bad_code.py"
        issues = parser.scan_file(str(fixture))
        long_funcs = [i for i in issues if i.type == "long_function"]
        assert len(long_funcs) >= 1, "应该检测出长函数"

    def test_todo_fixme_detection(self):
        parser = CodeParser()
        sample_dir = Path(__file__).parent.parent / "examples" / "sample_code"
        issues = parser.scan_directory(str(sample_dir))
        todos = [i for i in issues if i.type == "todo_fixme"]
        assert len(todos) > 0, "应该检测出 TODO/FIXME 标记"


class TestDiffGenerator:
    def test_generate_diff(self):
        suggestions = [
            RefactorSuggestion(
                file="test.py",
                original_lines="def f(a,b,c,d,e,f):\n    return a+b+c+d+e+f",
                new_lines="def f(*args):\n    return sum(args)",
                start_line=1,
                end_line=2,
                reason="参数过多，改用可变参数",
                confidence=0.9
            )
        ]
        diff = DiffGenerator.generate(suggestions)
        assert "--- a/test.py" in diff
        assert "+++ b/test.py" in diff
        assert "-def f(a,b,c,d,e,f)" in diff
        assert "+def f(*args)" in diff

    def test_generate_patch(self, tmp_path):
        suggestions = [
            RefactorSuggestion(
                file="test.py",
                original_lines="old",
                new_lines="new",
                start_line=1,
                end_line=1,
                reason="test",
                confidence=0.8
            )
        ]
        path = DiffGenerator.generate_patch_file(suggestions, str(tmp_path / "test.patch"))
        assert Path(path).exists()


class TestReportGenerator:
    def test_generate_report(self, tmp_path):
        gen = ReportGenerator(Path(tmp_path))
        path = gen.generate_pipeline_report(
            scan_issues=[
                {"file": "a.py", "line": 1, "severity": "high",
                 "type": "long_function", "description": "函数过长"}
            ],
            analysis_result={
                "summary": "测试摘要", "high_count": 1, "medium_count": 0,
                "low_count": 0, "overall_score": 70,
                "top_concern": "测试", "details": [], "refactor_priority": []
            },
            refactor_suggestions=[],
            review_result={"passed_count": 0, "total_count": 0, "score": "N/A", "verdict": "测试"}
        )
        assert Path(path).exists()
        content = Path(path).read_text(encoding="utf-8")
        assert "CodeForge" in content
        assert "long_function" in content or "函数过长" in content
