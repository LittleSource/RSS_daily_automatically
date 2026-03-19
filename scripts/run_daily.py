#!/usr/bin/env python3
"""
RSS日报推送 - 独立执行脚本
可直接在本地或GitHub Actions中运行
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import feedparser
import requests
from dateutil import parser as date_parser

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============= RSS源配置 =============
RSS_SOURCES = [
    # 科技媒体
    "https://rss.csdn.net/csdngeeknews/rss/map?spm=1001.2014.3001.5494",
    "https://sspai.com/feed",
    # 中文资讯
    "https://36kr.com/feed",
    "https://rsshub.52ym.vip/zhihu/hot",
    "https://rsshub.52ym.vip/weibo/search/hot/fulltext",
    "https://rsshub.52ym.vip/cls/depth/1000",
    # 加密货币
    "https://api.theblockbeats.news/v2/rss/newsflash",
    "https://rsshub.52ym.vip/twitter/user/Crypto_Cat888/readable=0&showEmojiForRetweetAndReply=1",
    "https://rsshub.52ym.vip/twitter/user/EmberCN/readable=0&showEmojiForRetweetAndReply=1"
    # 其他
    "https://rsshub.52ym.vip/bilibili/user/dynamic/285286947/showEmoji=1",
]

# 代理服务器配置
TELEGRAM_API_BASE_URL = os.getenv("TELEGRAM_API_BASE_URL", "https://api.telegram.org")


def fetch_rss_feeds(hours_filter: int = 24) -> List[Dict[str, Any]]:
    """
    从所有RSS源获取最近N小时的文章

    Args:
        hours_filter: 过滤最近N小时的文章，默认24小时

    Returns:
        文章列表
    """
    logger.info(f"开始获取RSS源，过滤最近{hours_filter}小时的文章...")

    all_articles: List[Dict[str, Any]] = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_filter)

    for rss_url in RSS_SOURCES:
        try:
            logger.info(f"获取: {rss_url}")
            feed = feedparser.parse(rss_url)

            source_name = feed.feed.get("title", "未知来源")

            for entry in feed.entries:
                try:
                    # 解析发布时间
                    published_str = (
                        entry.get("published")
                        or entry.get("updated")
                        or entry.get("pubDate")
                    )
                    if published_str:
                        published_time = date_parser.parse(published_str)
                        # 确保有时区信息
                        if published_time.tzinfo is None:
                            published_time = published_time.replace(tzinfo=timezone.utc)
                    else:
                        continue

                    # 过滤时间范围
                    if published_time < cutoff_time:
                        continue

                    article = {
                        "title": entry.get("title", "无标题"),
                        "link": entry.get("link", ""),
                        "published": published_str,
                        "summary": entry.get("summary", entry.get("description", ""))[
                            :200
                        ],
                        "source": source_name,
                        "published_time": published_time,
                    }

                    all_articles.append(article)

                except Exception as e:
                    logger.warning(f"解析文章失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"获取RSS源失败 {rss_url}: {e}")
            continue

    # 按时间排序
    all_articles.sort(key=lambda x: x["published_time"], reverse=True)

    logger.info(f"获取完成，共{len(all_articles)}篇文章")
    return all_articles


def call_llm_generate_report(articles: List[Dict[str, Any]]) -> str:
    """
    调用智谱AI大语言模型生成日报

    Args:
        articles: 文章列表

    Returns:
        生成的日报文本
    """
    logger.info("开始调用智谱AI生成日报...")

    # 获取API Key
    api_key = os.getenv("ZHIPUAI_API_KEY")
    if not api_key:
        raise ValueError("缺少智谱AI API Key：请设置 ZHIPUAI_API_KEY 环境变量")

    # 加载配置
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "generate_report_llm_cfg.json",
    )

    with open(config_path, "r", encoding="utf-8") as f:
        llm_config = json.load(f)

    # 准备文章摘要
    articles_text = ""
    for i, article in enumerate(articles[:50], 1):  # 最多50篇
        articles_text += f"{i}. 【{article['source']}】{article['title']}\n"
        articles_text += f"   链接: {article['link']}\n"
        if article["summary"]:
            articles_text += f"   摘要: {article['summary']}\n"
        articles_text += "\n"

    # 构建用户提示词
    user_prompt = f"""
请根据以下今日资讯生成一份结构化日报：

{articles_text}

要求：
1. 突出重要新闻和趋势
2. 分类整理（技术、科技、加密货币、热点等）
3. 推荐3-5篇最值得阅读的文章
4. 总结今日亮点和趋势
5. 使用emoji增加可读性
6. 输出HTML格式，使用合适的标签
"""

    # 调用智谱AI API
    try:
        from zhipuai import ZhipuAI

        client = ZhipuAI(api_key=api_key)

        response = client.chat.completions.create(
            model=llm_config["config"]["model"],
            messages=[
                {"role": "system", "content": llm_config["sp"]},
                {"role": "user", "content": user_prompt},
            ],
            temperature=llm_config["config"].get("temperature", 0.7),
            max_tokens=llm_config["config"].get("max_tokens", 4096),
            top_p=llm_config["config"].get("top_p", 0.9),
        )

        report = response.choices[0].message.content
        logger.info("日报生成成功")
        return report

    except Exception as e:
        logger.error(f"调用智谱AI失败: {e}")
        raise


def send_to_telegram(message: str) -> Dict[str, Any]:
    """
    发送消息到Telegram (支持超长消息自动拆分)

    Args:
        message: 要发送的消息内容（HTML格式）

    Returns:
        发送结果 (返回最后一条消息的结果)
    """
    logger.info("开始发送到Telegram...")

    # 获取环境变量
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise ValueError(
            "缺少Telegram配置：请设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 环境变量"
        )

    # Telegram 消息长度限制为 4096 字符，安全起见使用 4000
    MAX_LENGTH = 4000
    
    # 拆分消息
    messages = []
    if len(message) <= MAX_LENGTH:
        messages.append(message)
    else:
        logger.warning(f"消息长度({len(message)})超过限制，正在拆分发送...")
        # 按行拆分，尽量保持结构完整
        current_chunk = ""
        for line in message.split("\n"):
            if len(current_chunk) + len(line) + 1 > MAX_LENGTH:
                if current_chunk:
                    messages.append(current_chunk.strip())
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            messages.append(current_chunk.strip())

    # 构建API URL
    api_url = f"{TELEGRAM_API_BASE_URL}/bot{bot_token}/sendMessage"
    
    last_result = {"success": True}
    
    for i, msg in enumerate(messages):
        if len(messages) > 1:
            logger.info(f"发送第 {i+1}/{len(messages)} 部分...")
            
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(api_url, json=payload, timeout=30)
            if response.status_code != 200:
                logger.error(f"Telegram API 报错详情: {response.text}")
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                logger.info(f"✅ Telegram部分 {i+1} 推送成功")
                last_result = {"success": True, "message_id": result["result"]["message_id"]}
            else:
                logger.error(f"Telegram推送失败: {result}")
                return {
                    "success": False,
                    "error": result.get("description", "Unknown error"),
                }
        except Exception as e:
            logger.error(f"Telegram推送异常: {e}")
            raise
            
    return last_result


def format_report_for_telegram(report: str, article_count: int) -> str:
    """
    格式化日报为Telegram消息格式

    Args:
        report: 大模型生成的日报内容
        article_count: 文章总数

    Returns:
        格式化后的消息
    """
    # 添加日期和统计信息
    today = datetime.now().strftime("%Y年%m月%d日")

    header = f"""
<b>📅 {today} | 资讯日报</b>
"""

    return header + report


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("RSS日报推送任务开始")
    logger.info("=" * 50)

    try:
        # 1. 获取RSS文章
        hours_filter = int(os.getenv("HOURS_FILTER", "24"))
        articles = fetch_rss_feeds(hours_filter)

        if not articles:
            logger.warning("⚠️ 未获取到任何文章，可能是时间范围内无更新")
            # 发送提示消息
            send_to_telegram(
                f"<b>📰 今日资讯日报</b>\n\n"
                f"⚠️ 最近{hours_filter}小时暂无新文章更新\n\n"
                f"请检查RSS源是否正常"
            )
            return

        # 2. 生成日报
        report = call_llm_generate_report(articles)

        # 3. 格式化消息
        message = format_report_for_telegram(report, len(articles))

        # 4. 发送到Telegram
        result = send_to_telegram(message)

        if result.get("success"):
            logger.info("=" * 50)
            logger.info("✅ RSS日报推送成功！")
            logger.info(f"📊 文章数: {len(articles)}")
            logger.info(f"💬 消息ID: {result.get('message_id')}")
            logger.info("=" * 50)
        else:
            logger.error(f"❌ 推送失败: {result.get('error')}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ 任务执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
