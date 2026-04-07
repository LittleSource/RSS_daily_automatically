#!/usr/bin/env python3
"""
Test Telegram push configuration without importing RSS dependencies.
"""

import os
import sys

import requests


TELEGRAM_API_BASE_URL = os.getenv("TELEGRAM_API_BASE_URL", "https://api.telegram.org")


def send_to_telegram(message: str) -> dict:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise ValueError(
            "缺少 Telegram 配置：请设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID"
        )

    api_url = f"{TELEGRAM_API_BASE_URL}/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    response = requests.post(api_url, json=payload, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Telegram API 错误: {response.status_code} {response.text}")

    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(result.get("description", "Unknown error"))

    return {"success": True, "message_id": result["result"]["message_id"]}


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
