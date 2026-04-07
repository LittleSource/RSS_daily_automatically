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
from bs4 import BeautifulSoup, NavigableString
from dateutil import parser as date_parser
from markdown import markdown

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
DISCORD_API_BASE_URL = os.getenv("DISCORD_API_BASE_URL", "https://discord.com/api/v10")


def get_push_channel_status() -> Dict[str, bool]:
    """
    检查推送通道配置状态。
    """
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    telegram_any = bool(telegram_bot_token or telegram_chat_id)
    telegram_ready = bool(telegram_bot_token and telegram_chat_id)
    if telegram_any and not telegram_ready:
        raise ValueError(
            "Telegram 配置不完整：请同时设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID"
        )

    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
    discord_channel_id = os.getenv("DISCORD_CHANNEL_ID")
    discord_any = bool(discord_webhook_url or discord_bot_token or discord_channel_id)
    discord_ready = bool(discord_webhook_url) or bool(
        discord_bot_token and discord_channel_id
    )
    if discord_any and not discord_ready:
        raise ValueError(
            "Discord 配置不完整：请设置 DISCORD_WEBHOOK_URL，或同时设置 DISCORD_BOT_TOKEN 和 DISCORD_CHANNEL_ID"
        )

    if not telegram_ready and not discord_ready:
        raise ValueError(
            "未检测到可用推送通道：请配置 Telegram 或 Discord 的环境变量"
        )

    return {"telegram": telegram_ready, "discord": discord_ready}


def build_telegram_report_message(today: str, article_count: int, telegraph_url: str) -> str:
    """
    构建 Telegram 日报消息。
    """
    return f"""
<b>📰 {today} | 资讯日报已生成</b>

📌 今日共收录 {article_count} 篇文章。

🔗 <b>完整日报查看：</b>
{telegraph_url}
""".strip()


def build_discord_report_message(today: str, article_count: int, telegraph_url: str) -> str:
    """
    构建 Discord 日报消息。
    """
    return (
        f"## 📰 {today} | 资讯日报已生成\n\n"
        f"📌 今日共收录 **{article_count}** 篇文章。\n\n"
        f"🔗 完整日报：{telegraph_url}"
    )


def build_telegram_empty_message(hours_filter: int) -> str:
    """
    构建 Telegram 无更新提示。
    """
    return f"""
<b>📰 今日资讯日报</b>

⚠️ 最近 {hours_filter} 小时暂无新文章更新

请检查 RSS 源是否正常。
""".strip()


def build_discord_empty_message(hours_filter: int) -> str:
    """
    构建 Discord 无更新提示。
    """
    return (
        "## 📰 今日资讯日报\n\n"
        f"⚠️ 最近 **{hours_filter}** 小时暂无新文章更新。\n\n"
        "请检查 RSS 源是否正常。"
    )


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
        生成的日报文本 (Markdown格式)
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
6. 输出Markdown格式，使用合适的标题和列表
7. 有序列表必须写成 `1. 内容` 的单行格式，序号和内容之间不要换行
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


def html_to_telegraph_nodes(html: str) -> List[Any]:
    """
    将HTML字符串转换为Telegraph API所需的Node格式
    """
    soup = BeautifulSoup(html, "html.parser")

    def element_to_node(element):
        if isinstance(element, NavigableString):
            return str(element)
        
        if not hasattr(element, 'name'):
            return None

        # Telegraph 只支持特定的标签
        supported_tags = [
            "a", "aside", "b", "blockquote", "br", "code", "em",
            "figcaption", "figure", "h3", "h4", "hr", "i", "iframe",
            "img", "li", "ol", "p", "pre", "s", "strong", "u", "ul", "video"
        ]

        tag = element.name
        if tag in ["h1", "h2"]:
            tag = "h3"
        elif tag == "span" or tag == "div":
            # 对于不支持的容器标签，扁平化处理其子节点
            children = []
            for child in element.children:
                child_node = element_to_node(child)
                if child_node:
                    if isinstance(child_node, list):
                        children.extend(child_node)
                    else:
                        children.append(child_node)
            return children
        elif tag not in supported_tags:
            # 同样扁平化处理其他不支持的标签
            children = []
            for child in element.children:
                child_node = element_to_node(child)
                if child_node:
                    if isinstance(child_node, list):
                        children.extend(child_node)
                    else:
                        children.append(child_node)
            return children

        node = {"tag": tag, "children": []}
        
        # 属性处理
        if element.attrs:
            allowed_attrs = ["href", "src"]
            attrs = {k: v for k, v in element.attrs.items() if k in allowed_attrs}
            if attrs:
                node["attrs"] = attrs

        # Telegraph 对 li > p 的渲染会把序号和正文拆开显示，这里把段落拍平成同一项。
        if tag == "li":
            paragraph_count = 0
            for child in element.children:
                if getattr(child, "name", None) == "p":
                    if paragraph_count > 0 and node["children"]:
                        node["children"].append({"tag": "br"})
                        node["children"].append({"tag": "br"})

                    for paragraph_child in child.children:
                        paragraph_node = element_to_node(paragraph_child)
                        if paragraph_node:
                            if isinstance(paragraph_node, list):
                                node["children"].extend(paragraph_node)
                            else:
                                node["children"].append(paragraph_node)
                    paragraph_count += 1
                    continue

                child_node = element_to_node(child)
                if child_node:
                    if isinstance(child_node, list):
                        node["children"].extend(child_node)
                    else:
                        node["children"].append(child_node)
        else:
            # 子节点处理
            for child in element.children:
                child_node = element_to_node(child)
                if child_node:
                    if isinstance(child_node, list):
                        node["children"].extend(child_node)
                    else:
                        node["children"].append(child_node)
        
        if not node["children"]:
            del node["children"]

        return node

    nodes = []
    for child in soup.children:
        node = element_to_node(child)
        if isinstance(node, list):
            nodes.extend(node)
        elif node:
            nodes.append(node)

    return [n for n in nodes if n]


def upload_to_telegraph(title: str, md_content: str) -> str:
    """
    将Markdown内容上传到Telegraph
    """
    logger.info("开始上传到Telegraph...")

    try:
        # 1. 将Markdown转换为HTML
        html_content = markdown(md_content, extensions=["extra", "sane_lists"])

        # 2. 将HTML转换为Telegraph Nodes
        nodes = html_to_telegraph_nodes(html_content)

        # 3. 获取或创建Access Token
        access_token = os.getenv("TELEGRAPH_ACCESS_TOKEN")
        if not access_token:
            logger.info("未找到 TELEGRAPH_ACCESS_TOKEN，正在创建临时账号...")
            acc_res = requests.get(
                "https://api.telegra.ph/createAccount",
                params={"short_name": "RSSDaily", "author_name": "RSS Daily Bot"},
            ).json()
            if not acc_res.get("ok"):
                raise ValueError(f"创建Telegraph账号失败: {acc_res}")
            access_token = acc_res["result"]["access_token"]
            logger.info("临时账号创建成功")

        # 4. 创建页面
        page_res = requests.post(
            "https://api.telegra.ph/createPage",
            data={
                "access_token": access_token,
                "title": title,
                "content": json.dumps(nodes),
                "return_content": "false",
            },
        ).json()

        if page_res.get("ok"):
            url = page_res["result"]["url"]
            logger.info(f"Telegraph页面创建成功: {url}")
            return url
        else:
            logger.error(f"Telegraph页面创建失败: {page_res}")
            raise ValueError(f"Telegraph API 错误: {page_res.get('error')}")

    except Exception as e:
        logger.error(f"上传到Telegraph失败: {e}")
        raise


def send_to_telegram(message: str) -> Dict[str, Any]:
    """
    发送消息到Telegram
    """
    logger.info("开始发送到Telegram...")

    # 获取环境变量
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise ValueError(
            "缺少Telegram配置：请设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 环境变量"
        )

    # 构建API URL
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
        else:
            logger.error(f"Telegram推送失败: {result}")
            return {
                "success": False,
                "error": result.get("description", "Unknown error"),
            }
    except Exception as e:
        logger.error(f"Telegram推送异常: {e}")
        raise


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
    except Exception as e:
        logger.error(f"Discord推送异常: {e}")
        raise


def send_notifications(telegram_message: str, discord_message: str) -> Dict[str, Dict[str, Any]]:
    """
    发送消息到所有已配置的推送通道。
    """
    channel_status = get_push_channel_status()
    results: Dict[str, Dict[str, Any]] = {}

    if channel_status["telegram"]:
        results["telegram"] = send_to_telegram(telegram_message)

    if channel_status["discord"]:
        results["discord"] = send_to_discord(discord_message)

    return results


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
                f"<b>📅 今日资讯日报</b>\n\n"
                f"⚠️ 最近{hours_filter}小时暂无新文章更新\n\n"
                f"请检查RSS源是否正常"
            )
            return

        # 2. 生成日报 (Markdown格式)
        report_md = call_llm_generate_report(articles)

        # 3. 上传到Telegraph
        today = datetime.now().strftime("%Y年%m月%d日")
        title = f"{today} | 资讯日报"
        telegraph_url = upload_to_telegraph(title, report_md)

        # 4. 格式化并发送到Telegram (使用文本发送URL)
        tg_message = f"""
<b>📅 {today} | 资讯日报已生成</b>

🚀 今日共收录 {len(articles)} 篇文章。

🔗 <b>完整日报查看：</b>
{telegraph_url}
"""
        result = send_to_telegram(tg_message)

        if result.get("success"):
            logger.info("=" * 50)
            logger.info("✅ RSS日报推送成功！")
            logger.info(f"📊 文章数: {len(articles)}")
            logger.info(f"🔗 Telegraph URL: {telegraph_url}")
            logger.info("=" * 50)
        else:
            logger.error(f"❌ 推送失败: {result.get('error')}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ 任务执行失败: {e}", exc_info=True)
        sys.exit(1)

def main_v2():
    """主函数。"""
    logger.info("=" * 50)
    logger.info("RSS日报推送任务开始")
    logger.info("=" * 50)

    try:
        hours_filter = int(os.getenv("HOURS_FILTER", "24"))
        articles = fetch_rss_feeds(hours_filter)

        if not articles:
            logger.warning("⚠️ 未获取到任何文章，可能是时间范围内无更新")
            results = send_notifications(
                build_telegram_empty_message(hours_filter),
                build_discord_empty_message(hours_filter),
            )
            logger.info(f"空日报通知已发送: {', '.join(results.keys())}")
            return

        report_md = call_llm_generate_report(articles)

        today = datetime.now().strftime("%Y年%m月%d日")
        title = f"{today} | 资讯日报"
        telegraph_url = upload_to_telegraph(title, report_md)

        results = send_notifications(
            build_telegram_report_message(today, len(articles), telegraph_url),
            build_discord_report_message(today, len(articles), telegraph_url),
        )

        if all(result.get("success") for result in results.values()):
            logger.info("=" * 50)
            logger.info("✅ RSS日报推送成功！")
            logger.info(f"📰 文章数: {len(articles)}")
            logger.info(f"🔗 Telegraph URL: {telegraph_url}")
            logger.info(f"📨 推送通道: {', '.join(results.keys())}")
            logger.info("=" * 50)
        else:
            logger.error(f"❌ 推送失败: {results}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ 任务执行失败: {e}", exc_info=True)
        sys.exit(1)

main = main_v2


if __name__ == "__main__":
    main()
