#!/usr/bin/env python3
"""
Test Telegram push configuration without importing RSS dependencies.
"""

import os
import sys

from telegram_sender import send_to_telegram


def main() -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("❌ 缺少 Telegram 配置：请设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID")
        sys.exit(1)

    message = os.getenv(
        "TELEGRAM_TEST_MESSAGE",
        "<b>🧪 RSS日报 Telegram 通道测试成功。</b>",
    )

    try:
        result = send_to_telegram(message)
        print("✅ Telegram 测试成功")
        if result.get("message_id"):
            print(f"message_id: {result['message_id']}")
    except Exception as exc:
        print(f"❌ Telegram 测试失败: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
