#!/usr/bin/env python3
"""
测试Telegram配置是否正确
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from requests import post


def test_telegram_config():
    """测试Telegram配置"""
    print("=" * 50)
    print("Telegram配置测试")
    print("=" * 50)
    
    # 检查环境变量
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token:
        print("❌ 未设置 TELEGRAM_BOT_TOKEN 环境变量")
        print("   请执行: export TELEGRAM_BOT_TOKEN='your_token'")
        return False
    
    if not chat_id:
        print("❌ 未设置 TELEGRAM_CHAT_ID 环境变量")
        print("   请执行: export TELEGRAM_CHAT_ID='your_chat_id'")
        return False
    
    print(f"✅ TELEGRAM_BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ TELEGRAM_CHAT_ID: {chat_id}")
    
    # 测试发送消息
    api_base_url = os.getenv("TELEGRAM_API_BASE_URL", "http://f.52ym.vip/telegram")
    api_url = f"{api_base_url}/bot{bot_token}/sendMessage"
    
    print(f"\n📡 使用API服务器: {api_base_url}")
    print("\n正在发送测试消息...")
    
    payload = {
        "chat_id": chat_id,
        "text": "🧪 <b>配置测试成功！</b>\n\n✅ RSS日报机器人已准备就绪",
        "parse_mode": "HTML"
    }
    
    try:
        response = post(api_url, json=payload, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            print("\n" + "=" * 50)
            print("✅ 测试成功！")
            print("✅ Telegram消息已发送")
            print("=" * 50)
            print("\n请检查Telegram是否收到测试消息")
            return True
        else:
            print(f"\n❌ 发送失败: {result.get('description', 'Unknown error')}")
            print("\n可能的原因：")
            print("1. Bot Token 错误")
            print("2. Chat ID 错误")
            print("3. Bot 没有权限发送消息到该Chat")
            return False
            
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        print("\n可能的原因：")
        print("1. 网络连接问题")
        print("2. API服务器不可用")
        return False


if __name__ == "__main__":
    success = test_telegram_config()
    sys.exit(0 if success else 1)
