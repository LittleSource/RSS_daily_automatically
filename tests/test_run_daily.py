#!/usr/bin/env python3
"""
run_daily 核心逻辑测试。
"""

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

sys.modules.setdefault("feedparser", SimpleNamespace(parse=lambda *_args, **_kwargs: None))
sys.modules.setdefault(
    "dateutil",
    SimpleNamespace(parser=SimpleNamespace(parse=lambda *_args, **_kwargs: None)),
)
sys.modules.setdefault(
    "dateutil.parser",
    SimpleNamespace(parse=lambda *_args, **_kwargs: None),
)
sys.modules.setdefault(
    "discord_sender",
    SimpleNamespace(
        get_discord_config_status=lambda: {"any": False, "ready": False},
        send_to_discord=lambda _message: {"success": True},
    ),
)
sys.modules.setdefault(
    "telegram_sender",
    SimpleNamespace(
        get_telegram_config_status=lambda: {"any": False, "ready": False},
        send_to_telegram=lambda _message: {"success": True},
    ),
)
sys.modules.setdefault(
    "wechat_sender",
    SimpleNamespace(
        get_wechat_config_status=lambda: {"any": False, "ready": False},
        send_to_wechat=lambda _message: {"success": True},
    ),
)

import run_daily


def make_choice(content: str, finish_reason: str):
    return SimpleNamespace(
        message=SimpleNamespace(content=content),
        finish_reason=finish_reason,
    )


class FakeCompletions:
    def __init__(self, choices):
        self._choices = list(choices)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._choices:
            raise AssertionError("没有更多模拟响应可用")

        return SimpleNamespace(choices=[self._choices.pop(0)])


class FakeClient:
    def __init__(self, choices):
        self.chat = SimpleNamespace(completions=FakeCompletions(choices))


class RunDailyTests(unittest.TestCase):
    def test_merge_markdown_chunks_removes_overlap(self):
        merged = run_daily.merge_markdown_chunks(
            "• [美以袭击伊朗进入第 64 天，",
            "• [美以袭击伊朗进入第 64 天，以军继续扩大行动](https://example.com)",
        )

        self.assertEqual(
            merged,
            "• [美以袭击伊朗进入第 64 天，以军继续扩大行动](https://example.com)",
        )

    def test_generate_report_with_continuation_continues_after_length(self):
        client = FakeClient(
            [
                make_choice("今日资讯概览\n\n• 第一段", "length"),
                make_choice("• 第一段补全\n\n💡 今日亮点\n市场继续升温", "stop"),
            ]
        )
        llm_config = {
            "config": {"model": "glm-test", "temperature": 0.7, "top_p": 0.9},
            "sp": "system prompt",
        }

        with patch.dict(os.environ, {"LLM_MAX_TOKENS": "9000"}, clear=False):
            result = run_daily.generate_report_with_continuation(
                client=client,
                llm_config=llm_config,
                user_prompt="user prompt",
            )

        self.assertIn("今日资讯概览", result)
        self.assertIn("💡 今日亮点", result)
        self.assertEqual(result.count("• 第一段"), 1)
        self.assertEqual(len(client.chat.completions.calls), 2)

    def test_normalize_report_markdown_removes_code_fence_and_hot_numbers(self):
        content = """```markdown
🔥 热门推荐
1. [标题一](https://example.com/1)
2. [标题二](https://example.com/2)

📚 分类资讯
```"""

        result = run_daily.normalize_report_markdown(content)

        self.assertNotIn("```", result)
        self.assertNotIn("1. ", result)
        self.assertNotIn("2. ", result)
        self.assertIn("• [标题一]", result)


if __name__ == "__main__":
    unittest.main()
