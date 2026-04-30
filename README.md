# CodeForge — 多 Agent 协作代码审查&重构流水线

基于多 AI Agent 协作的自动化代码质量审查和重构方案生成系统。通过 **Scanner → Analyzer → Refactor → Reviewer** 四个专业 Agent 的长链推理协作，实现端到端的代码技术债检测和自动重构。

## 架构

```
[代码仓库] → Scanner → Analyzer → Refactor → Reviewer → [重构报告 + Patch]
              ↑_________________上下文传递________________↑
```

### 四个 Agent 协作流程

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| **Scanner** | 代码异味扫描 | 源代码目录 | 结构化问题列表 |
| **Analyzer** | 深度分析 & 优先级排序 | Scanner 输出 | 分析报告 + 优先级 |
| **Refactor** | 生成重构方案 | Analyzer 输出 | 具体重构代码(diff) |
| **Reviewer** | 审查验证方案 | Refactor 输出 | 审查报告 + 评分 |

### 长链推理特点

- 每个 Agent 的输出是下一个 Agent 的输入，形成完整推理链条
- AST 静态分析 + LLM 语义分析互补
- 多 Provider 支持 (Claude / GPT) 自动 fallback

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY 或 OPENAI_API_KEY
```

### 3. 运行

```bash
# 完整多 Agent 协作模式
python -m src.main --target examples/sample_code/

# 仅 AST 扫描模式 (无需 API Key)
python -m src.main --target examples/sample_code/ --no-ai
```

### 4. 查看报告

报告生成在 `reports/` 目录下，Markdown 格式。

## 运行测试

```bash
pytest tests/ -v
```

## 项目结构

```
src/
├── main.py              # CLI 入口
├── orchestrator.py      # 多 Agent 编排引擎
├── config.py            # 配置管理
├── agents/              # 四个专业 Agent
│   ├── base.py          # Agent 基类
│   ├── scanner.py       # 扫描 Agent
│   ├── analyzer.py      # 分析 Agent
│   ├── refactor.py      # 重构 Agent
│   └── reviewer.py      # 审查 Agent
└── tools/               # 工具模块
    ├── code_parser.py   # AST 代码解析
    ├── diff_gen.py      # Diff 生成
    └── report.py        # 报告生成
```

## 检测的代码异味

- 长函数（超过 50 行）
- 高圈复杂度（超过 10）
- 参数过多（超过 5 个）
- 深层嵌套（超过 4 层）
- 裸 except
- 重复代码模式
- TODO/FIXME 遗留标记
- 疑似 SQL 注入
- 命名不清晰（AI 辅助判断）
