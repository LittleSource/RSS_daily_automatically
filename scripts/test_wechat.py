#!/usr/bin/env python3
"""
Test WeChat push configuration via GeWe without importing RSS dependencies.
"""

import os
import sys

from wechat_sender import send_to_wechat


def main() -> None:
    token = os.getenv("GEWE_TOKEN")
    app_id = os.getenv("GEWE_APP_ID")
    to_wxid = os.getenv("WECHAT_TO_WXID")

    if not token or not app_id or not to_wxid:
        print(
            "❌ 缺少微信配置：请设置 GEWE_TOKEN、GEWE_APP_ID 和 WECHAT_TO_WXID"
        )
        sys.exit(1)

    message = os.getenv("WECHAT_TEST_MESSAGE", "🧪 RSS日报 微信通道测试成功。")

    try:
        result = send_to_wechat(message)
        print("✅ 微信测试成功")
        if result.get("message_id"):
            print(f"message_id: {result['message_id']}")
    except Exception as exc:
        print(f"❌ 微信测试失败: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
