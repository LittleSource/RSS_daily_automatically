#!/usr/bin/env python3
"""
Discord 推送能力封装。
"""

import logging
import os
from typing import Any, Dict

import requests


logger = logging.getLogger(__name__)

DISCORD_API_BASE_URL = os.getenv("DISCORD_API_BASE_URL", "https://discord.com/api/v10")


def get_discord_config_status() -> Dict[str, bool]:
    """
    返回 Discord 配置状态。
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    channel_id = os.getenv("DISCORD_CHANNEL_ID")

    return {
        "any": bool(webhook_url or bot_token or channel_id),
        "ready": bool(webhook_url) or bool(bot_token and channel_id),
    }


def send_to_discord(message: str) -> Dict[str, Any]:
    """
    发送消息到 Discord。
    """
    logger.info("开始发送到Discord...")

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
            "缺少Discord配置：请设置 DISCORD_WEBHOOK_URL，或同时设置 DISCORD_BOT_TOKEN 和 DISCORD_CHANNEL_ID"
        )

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        if response.status_code not in (200, 204):
            logger.error(f"Discord API 报错详情: {response.text}")
        response.raise_for_status()

        if response.status_code == 204:
            logger.info("✅ Discord 推送成功")
            return {"success": True}

        result = response.json()
        logger.info("✅ Discord 推送成功")
        return {"success": True, "message_id": result.get("id")}
    except Exception as exc:
        logger.error(f"Discord推送异常: {exc}")
        raise
