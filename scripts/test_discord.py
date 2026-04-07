#!/usr/bin/env python3
"""
Test Discord push configuration without importing RSS dependencies.
"""

import os
import sys

import requests


DISCORD_API_BASE_URL = os.getenv("DISCORD_API_BASE_URL", "https://discord.com/api/v10")


def send_to_discord(message: str) -> dict:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    channel_id = os.getenv("DISCORD_CHANNEL_ID")

    headers = {"Content-Type": "application/json"}
    payload = {"content": message}

    if webhook_url:
        api_url = webhook_url
    elif bot_token and channel_id:
        api_url = f"{DISCORD_API_BASE_URL}/channels/{channel_id}/messages"
        headers["Authorization"] = f"Bot {bot_token}"
    else:
        raise ValueError(
            "缺少 Discord 配置：请设置 DISCORD_WEBHOOK_URL，"
            "或同时设置 DISCORD_BOT_TOKEN 和 DISCORD_CHANNEL_ID"
        )

    response = requests.post(api_url, json=payload, headers=headers, timeout=30)
    if response.status_code not in (200, 204):
        raise RuntimeError(f"Discord API 错误: {response.status_code} {response.text}")

    if response.status_code == 204:
        return {"success": True}

    result = response.json()
    return {"success": True, "message_id": result.get("id")}


def main() -> None:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    channel_id = os.getenv("DISCORD_CHANNEL_ID")

    if not webhook_url and not (bot_token and channel_id):
        print(
            "❌ 缺少 Discord 配置：请设置 DISCORD_WEBHOOK_URL，"
            "或同时设置 DISCORD_BOT_TOKEN 和 DISCORD_CHANNEL_ID"
        )
        sys.exit(1)

    message = os.getenv("DISCORD_TEST_MESSAGE", "🧪 RSS日报 Discord 通道测试成功。")

    try:
        result = send_to_discord(message)
        print("✅ Discord 测试成功")
        if result.get("message_id"):
            print(f"message_id: {result['message_id']}")
    except Exception as exc:
        print(f"❌ Discord 测试失败: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
