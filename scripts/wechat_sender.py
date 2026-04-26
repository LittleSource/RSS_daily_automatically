#!/usr/bin/env python3
"""
微信（GeWe）推送能力封装。
"""

import logging
import os
from typing import Any, Dict

import requests


logger = logging.getLogger(__name__)

GEWE_API_BASE_URL = os.getenv("GEWE_API_BASE_URL", "http://api.geweapi.com")


def get_wechat_config_status() -> Dict[str, bool]:
    """
    返回微信（GeWe）配置状态。
    """
    token = os.getenv("GEWE_TOKEN")
    app_id = os.getenv("GEWE_APP_ID")
    to_wxid = os.getenv("WECHAT_TO_WXID")

    return {
        "any": bool(token or app_id or to_wxid),
        "ready": bool(token and app_id and to_wxid),
    }


def send_to_wechat(message: str) -> Dict[str, Any]:
    """
    通过 GeWe 发送微信文本消息。
    参考文档: https://doc.geweapi.com/api-139908313
    """
    logger.info("开始发送到微信(GeWe)...")

    token = os.getenv("GEWE_TOKEN")
    app_id = os.getenv("GEWE_APP_ID")
    to_wxid = os.getenv("WECHAT_TO_WXID")

    if not token or not app_id or not to_wxid:
        raise ValueError(
            "缺少微信配置：请设置 GEWE_TOKEN、GEWE_APP_ID 和 WECHAT_TO_WXID 环境变量"
        )

    api_url = f"{GEWE_API_BASE_URL}/gewe/v2/api/message/postText"
    headers = {
        "X-GEWE-TOKEN": token,
        "Content-Type": "application/json",
    }
    payload = {
        "appId": app_id,
        "toWxid": to_wxid,
        "content": message,
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        if response.status_code != 200:
            logger.error(f"GeWe API 报错详情: {response.text}")
        response.raise_for_status()
        result = response.json()

        if result.get("ret") == 200:
            logger.info("✅ 微信(GeWe) 推送成功")
            data = result.get("data", {})
            return {
                "success": True,
                "message_id": data.get("newMsgId") or data.get("msgId"),
            }

        logger.error(f"微信(GeWe)推送失败: {result}")
        return {
            "success": False,
            "error": result.get("msg", "Unknown error"),
        }
    except Exception as exc:
        logger.error(f"微信(GeWe)推送异常: {exc}")
        raise
