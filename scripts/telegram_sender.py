#!/usr/bin/env python3
"""
Telegram 推送能力封装。
"""

import logging
import os
from typing import Any, Dict

import requests


logger = logging.getLogger(__name__)

TELEGRAM_API_BASE_URL = os.getenv("TELEGRAM_API_BASE_URL", "https://api.telegram.org")


def get_telegram_config_status() -> Dict[str, bool]:
    """
    返回 Telegram 配置状态。
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    return {
        "any": bool(bot_token or chat_id),
        "ready": bool(bot_token and chat_id),
    }


def send_to_telegram(message: str) -> Dict[str, Any]:
    """
    发送消息到 Telegram。
    """
    logger.info("开始发送到Telegram...")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise ValueError(
            "缺少Telegram配置：请设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 环境变量"
        )

    api_url = f"{TELEGRAM_API_BASE_URL}/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(api_url, json=payload, timeout=30)
        if response.status_code != 200:
            logger.error(f"Telegram API 报错详情: {response.text}")
        response.raise_for_status()
        result = response.json()

        if result.get("ok"):
            logger.info("✅ Telegram 推送成功")
            return {"success": True, "message_id": result["result"]["message_id"]}

        logger.error(f"Telegram推送失败: {result}")
        return {
            "success": False,
            "error": result.get("description", "Unknown error"),
        }
    except Exception as exc:
        logger.error(f"Telegram推送异常: {exc}")
        raise
