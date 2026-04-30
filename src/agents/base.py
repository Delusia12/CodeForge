"""Agent 基类 - 封装 AI API 调用、重试、多 Provider 支持"""

import json
from typing import Optional
from abc import ABC, abstractmethod

import src.config as cfg


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""

    def __init__(self, model: str | None = None):
        self.model = model or cfg.DEFAULT_MODEL
        self._messages: list[dict] = []

    @abstractmethod
    def system_prompt(self) -> str:
        """每个 Agent 自己定义系统提示词"""
        ...

    def _call_anthropic(self, user_message: str) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=cfg.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt(),
            messages=[{"role": "user", "content": user_message}],
        )
        return resp.content[0].text

    def _call_openai(self, user_message: str) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=cfg.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=cfg.FALLBACK_MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt()},
                {"role": "user", "content": user_message},
            ],
            max_tokens=4096,
        )
        return resp.choices[0].message.content or ""

    def ask(self, user_message: str) -> str:
        """调用 AI API，自动 fallback"""
        if cfg.ANTHROPIC_API_KEY:
            try:
                return self._call_anthropic(user_message)
            except Exception as e:
                print(f"  [warn] Anthropic API 失败: {e}, 尝试 OpenAI fallback...")
        if cfg.OPENAI_API_KEY:
            return self._call_openai(user_message)
        raise RuntimeError("没有可用的 AI API Key，请配置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY")

    def ask_json(self, user_message: str) -> dict | list:
        """调用并解析 JSON 返回"""
        text = self.ask(user_message)
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:] if lines[0].startswith("```") else lines
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)

    def status_line(self, msg: str):
        print(f"  [{self.name}] {msg}")
