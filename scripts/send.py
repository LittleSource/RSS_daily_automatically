#!/usr/bin/env python3
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import feedparser
import requests
from dateutil import parser as date_parser
from discord_sender import get_discord_config_status, send_to_discord
from telegram_sender import get_telegram_config_status, send_to_telegram
from wechat_sender import get_wechat_config_status, send_to_wechat

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def build_wechat_report_message(today: str,  report_url: str) -> str:
    """
    构建微信日报消息。
    """
    return (
        f"📰 {today} | 资讯日报\n\n"
        f"🔗 完整日报：{report_url}"
    )

def main():
    """主函数。"""
    logger.info("=" * 50)
    logger.info("RSS日报推送任务开始")
    logger.info("=" * 50)

    try:
        today_date = datetime.now()
        today = today_date.strftime("%Y年%m月%d日")
        report_url = today_date.strftime("https://littlesource.github.io/Horizon/%Y/%m/%d/summary-zh.html")
        result = send_to_wechat(build_wechat_report_message(today, report_url))

        if result.get("success"):
            logger.info("=" * 50)
            logger.info("✅ 资讯日报推送成功！")
            logger.info("=" * 50)
        else:
            logger.error(f"❌ 推送失败: {result}")
            sys.exit(1)

        # result = send_to_wechat("药店签到", 2)

        # if result.get("success"):
        #     logger.info("=" * 50)
        #     logger.info("✅ 药店签到推送成功！")
        #     logger.info("=" * 50)
        # else:
        #     logger.error(f"❌ 推送失败: {result}")
        #     sys.exit(1)

    except Exception as e:
        logger.error(f"❌ 任务执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
