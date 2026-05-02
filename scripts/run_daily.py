#!/usr/bin/env python3
"""
RSS日报推送 - 独立执行脚本
可直接在本地或GitHub Actions中运行
"""

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
    "https://imjuya.github.io/juya-ai-daily/rss.xml",
]

SUPPORTED_PUSH_CHANNELS = ("telegram", "discord", "wechat")
DEFAULT_LLM_MAX_TOKENS = 8192
DEFAULT_LLM_CONTINUATION_ROUNDS = 3
DEFAULT_LLM_ARTICLE_LIMIT = 50


def get_selected_push_channel() -> str:
    """
    获取当前显式指定的推送渠道。
    """
    push_channel = os.getenv("PUSH_CHANNEL", "").strip().lower()

    if not push_channel:
        raise ValueError(
            "未设置 PUSH_CHANNEL 环境变量：请显式指定 telegram、discord 或 wechat"
        )

    if push_channel not in SUPPORTED_PUSH_CHANNELS:
        raise ValueError(
            "无效的 PUSH_CHANNEL 环境变量："
            f"{push_channel}。仅支持 telegram、discord 或 wechat"
        )

    return push_channel


def get_push_channel_status() -> Dict[str, bool]:
    """
    检查显式指定的推送通道配置状态。
    """
    push_channel = get_selected_push_channel()

    telegram_status = get_telegram_config_status()
    telegram_any = telegram_status["any"]
    telegram_ready = telegram_status["ready"]
    if push_channel == "telegram" and telegram_any and not telegram_ready:
        raise ValueError(
            "Telegram 配置不完整：请同时设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID"
        )

    discord_status = get_discord_config_status()
    discord_any = discord_status["any"]
    discord_ready = discord_status["ready"]
    if push_channel == "discord" and discord_any and not discord_ready:
        raise ValueError(
            "Discord 配置不完整：请设置 DISCORD_WEBHOOK_URL，或同时设置 DISCORD_BOT_TOKEN 和 DISCORD_CHANNEL_ID"
        )

    wechat_status = get_wechat_config_status()
    wechat_any = wechat_status["any"]
    wechat_ready = wechat_status["ready"]
    if push_channel == "wechat" and wechat_any and not wechat_ready:
        raise ValueError(
            "微信配置不完整：请同时设置 GEWE_TOKEN、GEWE_APP_ID 和 WECHAT_TO_WXID"
        )

    if push_channel == "telegram" and not telegram_ready:
        raise ValueError(
            "PUSH_CHANNEL=telegram，但未检测到完整 Telegram 配置："
            "请设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID"
        )

    if push_channel == "discord" and not discord_ready:
        raise ValueError(
            "PUSH_CHANNEL=discord，但未检测到完整 Discord 配置："
            "请设置 DISCORD_WEBHOOK_URL，或同时设置 DISCORD_BOT_TOKEN 和 DISCORD_CHANNEL_ID"
        )

    if push_channel == "wechat" and not wechat_ready:
        raise ValueError(
            "PUSH_CHANNEL=wechat，但未检测到完整微信配置："
            "请设置 GEWE_TOKEN、GEWE_APP_ID 和 WECHAT_TO_WXID"
        )

    return {
        "telegram": push_channel == "telegram" and telegram_ready,
        "discord": push_channel == "discord" and discord_ready,
        "wechat": push_channel == "wechat" and wechat_ready,
    }


def build_telegram_report_message(
    today: str, article_count: int, report_url: str
) -> str:
    """
    构建 Telegram 日报消息。
    """
    return f"""
<b>📰 {today} | 资讯日报已生成</b>

📌 今日共收录 {article_count} 篇文章。

🔗 <b>完整日报查看：</b>
{report_url}
""".strip()


def build_discord_report_message(
    today: str, article_count: int, report_url: str
) -> str:
    """
    构建 Discord 日报消息。
    """
    return (
        f"## 📰 {today} | 资讯日报已生成\n\n"
        f"📌 今日共收录 **{article_count}** 篇文章。\n\n"
        f"🔗 完整日报：{report_url}"
    )


def build_wechat_report_message(today: str, article_count: int, report_url: str) -> str:
    """
    构建微信日报消息。
    """
    return (
        f"📰 {today} | 资讯日报已生成\n\n"
        f"📌 今日共收录 {article_count} 篇文章。\n\n"
        f"🔗 完整日报：{report_url}"
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


def build_wechat_empty_message(hours_filter: int) -> str:
    """
    构建微信无更新提示。
    """
    return (
        "📰 今日资讯日报\n\n"
        f"⚠️ 最近 {hours_filter} 小时暂无新文章更新。\n\n"
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
    article_limit = int(
        os.getenv("LLM_ARTICLE_LIMIT", str(DEFAULT_LLM_ARTICLE_LIMIT))
    )
    articles_text = build_articles_text(articles, limit=article_limit)

    # 构建用户提示词
    user_prompt = build_report_user_prompt(articles_text)

    # 调用智谱AI API
    try:
        from zhipuai import ZhipuAI

        client = ZhipuAI(api_key=api_key)

        report = generate_report_with_continuation(
            client=client,
            llm_config=llm_config,
            user_prompt=user_prompt,
        )
        if not report:
            logger.warning("智谱AI返回空内容，使用默认日报模板")
            report = _build_default_report(articles)
        logger.info("日报生成成功")
        return report

    except Exception as e:
        logger.error(f"调用智谱AI失败: {e}")
        raise


def _build_default_report(articles: List[Dict[str, Any]]) -> str:
    """
    当智谱AI返回空内容时，生成一个简单的默认日报。
    """
    from datetime import datetime

    today = datetime.now().strftime("%Y年%m月%d日")
    lines = [f"# 📰 {today} | 资讯日报\n"]
    lines.append(f"> 今日共获取 **{len(articles)}** 篇资讯\n")
    lines.append("---\n")

    # 按来源分组
    sources: Dict[str, List[Dict[str, Any]]] = {}
    for article in articles:
        src = article.get("source", "未知")
        sources.setdefault(src, []).append(article)

    for src, src_articles in sources.items():
        lines.append(f"## {src}\n")
        for article in src_articles:
            lines.append(f"- [{article['title']}]({article['link']})")
            if article.get("summary"):
                lines.append(f"  - {article['summary'][:100]}")
        lines.append("")

    lines.append("---\n")
    lines.append("*由 RSS日报自动推送 自动生成*")
    return "\n".join(lines)


def build_articles_text(articles: List[Dict[str, Any]], limit: int) -> str:
    """
    将文章列表整理为传给大模型的纯文本。
    """
    article_chunks: List[str] = []
    for i, article in enumerate(articles[:limit], 1):
        article_chunks.append(f"{i}. 【{article['source']}】{article['title']}")
        article_chunks.append(f"   链接: {article['link']}")
        if article["summary"]:
            article_chunks.append(f"   摘要: {article['summary']}")
        article_chunks.append("")

    return "\n".join(article_chunks)


def build_report_user_prompt(articles_text: str) -> str:
    """
    构建日报生成提示词。
    """
    return f"""
请根据以下今日资讯生成一份结构化日报：

{articles_text}

要求：
1. 突出重要新闻和趋势
2. 分类整理（技术、科技、加密货币、热点等）
3. 推荐3-5篇最值得阅读的文章
4. 总结今日亮点和趋势
5. 使用emoji增加可读性
6. 输出Markdown格式，使用合适的标题和列表
7. “🔥 热门推荐”部分不要使用任何数字序号，使用无序列表或单独换行展示即可
8. 如果内容较长，也必须完整输出，不要在中间省略或截断
""".strip()


def resolve_llm_max_tokens(llm_config: Dict[str, Any]) -> int:
    """
    获取大模型输出 token 上限，支持环境变量覆盖。
    """
    raw_value = os.getenv("LLM_MAX_TOKENS")
    if raw_value:
        return int(raw_value)

    configured_value = llm_config["config"].get("max_tokens", DEFAULT_LLM_MAX_TOKENS)
    return max(int(configured_value), DEFAULT_LLM_MAX_TOKENS)


def extract_choice_content(choice: Any) -> str:
    """
    兼容不同 SDK 响应结构，提取文本内容。
    """
    message = getattr(choice, "message", None)
    if message is None and isinstance(choice, dict):
        message = choice.get("message", {})

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content", "")

    if isinstance(content, list):
        text_parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
                continue

            if isinstance(item, dict):
                text_parts.append(str(item.get("text", "")))
                continue

            text_parts.append(str(getattr(item, "text", "")))

        return "".join(text_parts).strip()

    return str(content or "").strip()


def extract_finish_reason(choice: Any) -> str:
    """
    提取大模型停止原因。
    """
    finish_reason = getattr(choice, "finish_reason", None)
    if finish_reason is None and isinstance(choice, dict):
        finish_reason = choice.get("finish_reason", "")

    return str(finish_reason or "").strip().lower()


def should_continue_generation(finish_reason: str) -> bool:
    """
    判断是否需要继续生成剩余内容。
    """
    return finish_reason in {"length", "max_tokens"}


def merge_markdown_chunks(base: str, continuation: str) -> str:
    """
    合并被截断的 Markdown 片段，尽量去掉重复前缀。
    """
    base_clean = base.rstrip()
    continuation_clean = continuation.lstrip()

    if not base_clean:
        return continuation_clean
    if not continuation_clean:
        return base_clean

    max_overlap = min(len(base_clean), len(continuation_clean), 200)
    overlap_found = False
    for overlap_size in range(max_overlap, 2, -1):
        if base_clean.endswith(continuation_clean[:overlap_size]):
            continuation_clean = continuation_clean[overlap_size:]
            overlap_found = True
            break

    if not continuation_clean:
        return base_clean

    if overlap_found:
        return f"{base_clean}{continuation_clean}"

    if base_clean.endswith("\n") or continuation_clean.startswith("\n"):
        return f"{base_clean}{continuation_clean}"

    return f"{base_clean}\n{continuation_clean}"


def generate_report_with_continuation(
    client: Any, llm_config: Dict[str, Any], user_prompt: str
) -> str:
    """
    调用大模型生成日报；若因长度截断则自动续写。
    """
    max_tokens = resolve_llm_max_tokens(llm_config)
    continuation_rounds = int(
        os.getenv("LLM_CONTINUATION_ROUNDS", str(DEFAULT_LLM_CONTINUATION_ROUNDS))
    )
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": llm_config["sp"]},
        {"role": "user", "content": user_prompt},
    ]
    report = ""

    for attempt in range(continuation_rounds + 1):
        response = client.chat.completions.create(
            model=llm_config["config"]["model"],
            messages=messages,
            temperature=llm_config["config"].get("temperature", 0.7),
            max_tokens=max_tokens,
            top_p=llm_config["config"].get("top_p", 0.9),
        )
        choice = response.choices[0]
        chunk = extract_choice_content(choice)
        finish_reason = extract_finish_reason(choice)

        logger.info(
            "LLM 输出片段完成：attempt=%s finish_reason=%s chars=%s",
            attempt + 1,
            finish_reason or "unknown",
            len(chunk),
        )

        report = merge_markdown_chunks(report, chunk)
        if not should_continue_generation(finish_reason):
            break

        messages.extend(
            [
                {"role": "assistant", "content": chunk},
                {
                    "role": "user",
                    "content": (
                        "你刚才的输出因为长度限制被截断了。"
                        "请从中断处继续补全剩余 Markdown，"
                        "不要重新开头，不要重复已经完整输出的部分。"
                        "如果最后一行被截断，请从该行开头重写该行后继续。"
                    ),
                },
            ]
        )
    else:
        logger.warning("LLM 已达到最大续写轮次，日报可能仍然不完整")

    return report


def normalize_report_markdown(md_content: str) -> str:
    """
    规范化日报 Markdown，去掉代码块包裹，并清理热门推荐中的序号。
    """
    stripped_content = md_content.strip()
    fenced_match = re.fullmatch(
        r"```(?:markdown|md)?\s*\n?(.*?)\n?```", stripped_content, flags=re.DOTALL
    )
    if fenced_match:
        md_content = fenced_match.group(1).strip()

    lines = md_content.splitlines()
    normalized_lines: List[str] = []
    in_hot_section = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("🔥 热门推荐"):
            in_hot_section = True
            normalized_lines.append(line)
            continue

        if in_hot_section and (
            stripped.startswith("#")
            or stripped.startswith("📚 ")
            or stripped.startswith("💡 ")
            or stripped.startswith("今日亮点")
        ):
            in_hot_section = False

        if in_hot_section and stripped:
            stripped = re.sub(r"^\d+\.\s*", "", stripped)
            stripped = re.sub(r"^\d+[、.)]\s*", "", stripped)
            stripped = re.sub(
                r"^(?:\d️⃣|🔟|[①②③④⑤⑥⑦⑧⑨⑩]|[1-9][\uFE0F\u20E3])\s*",
                "",
                stripped,
            )
            stripped = re.sub(r"^[-*+]\s*", "", stripped)
            line = f"• {stripped}"

        normalized_lines.append(line)

    return "\n".join(normalized_lines)


def parse_env_bool(env_name: str, default: bool = False) -> bool:
    """
    解析环境变量布尔值。
    """
    raw_value = os.getenv(env_name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def build_gist_filename() -> str:
    """
    生成 Gist 文件名。
    """
    filename = os.getenv("GIST_FILENAME", "").strip()
    if not filename:
        filename = f"{datetime.now().strftime('%Y%m%d')}.md"

    if not filename.endswith(".md"):
        filename = f"{filename}.md"

    if re.fullmatch(r"gistfile\d*", filename):
        raise ValueError(
            "GIST_FILENAME 不能使用 gistfile 或 gistfile123 这类名称，请换一个自定义文件名"
        )

    return filename


def upload_to_github_gist(title: str, md_content: str) -> str:
    """
    将 Markdown 内容上传到 GitHub Gist，并返回可访问页面地址。
    """
    logger.info("开始上传到 GitHub Gist...")

    try:
        if not md_content:
            raise ValueError("Markdown 内容为空，无法上传到 GitHub Gist")

        access_token = os.getenv("GIST_GITHUB_TOKEN", "").strip()
        if not access_token:
            raise ValueError(
                "缺少 GitHub Gist Token：请设置 GIST_GITHUB_TOKEN 环境变量"
            )

        filename = build_gist_filename()
        is_public = parse_env_bool("GIST_PUBLIC", default=True)
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        response = requests.post(
            "https://api.github.com/gists",
            headers=headers,
            json={
                "description": title,
                "public": is_public,
                "files": {filename: {"content": md_content}},
            },
            timeout=30,
        )
        if response.status_code != 201:
            error_message = response.text.strip()
            logger.error(
                f"GitHub Gist 创建失败: status={response.status_code}, body={error_message}"
            )
            raise ValueError(
                f"GitHub Gist API 错误（HTTP {response.status_code}）: {error_message}"
            )

        gist_res = response.json()
        url = (gist_res.get("html_url") or "").strip()
        if not url:
            raise ValueError("GitHub Gist API 未返回 html_url")

        logger.info(f"GitHub Gist 创建成功: {url}")
        return url

    except Exception as e:
        logger.error(f"上传到 GitHub Gist 失败: {e}")
        raise


def send_notifications(
    telegram_message: str, discord_message: str, wechat_message: str
) -> Dict[str, Dict[str, Any]]:
    """
    发送消息到显式指定的推送通道。
    """
    push_channel = get_selected_push_channel()
    channel_status = get_push_channel_status()
    results: Dict[str, Dict[str, Any]] = {}

    if channel_status["telegram"]:
        results["telegram"] = send_to_telegram(telegram_message)

    if channel_status["discord"]:
        results["discord"] = send_to_discord(discord_message)

    if channel_status["wechat"]:
        results["wechat"] = send_to_wechat(wechat_message)

    logger.info(f"当前推送渠道: {push_channel}")
    return results


def main():
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
                build_wechat_empty_message(hours_filter),
            )
            logger.info(f"空日报通知已发送: {', '.join(results.keys())}")
            return

        report_md = normalize_report_markdown(call_llm_generate_report(articles))

        today = datetime.now().strftime("%Y年%m月%d日")
        title = f"{today} | 资讯日报"
        report_url = upload_to_github_gist(title, report_md)

        results = send_notifications(
            build_telegram_report_message(today, len(articles), report_url),
            build_discord_report_message(today, len(articles), report_url),
            build_wechat_report_message(today, len(articles), report_url),
        )

        if all(result.get("success") for result in results.values()):
            logger.info("=" * 50)
            logger.info("✅ RSS日报推送成功！")
            logger.info(f"📰 文章数: {len(articles)}")
            logger.info(f"🔗 Gist URL: {report_url}")
            logger.info(f"📨 推送通道: {', '.join(results.keys())}")
            logger.info("=" * 50)
        else:
            logger.error(f"❌ 推送失败: {results}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ 任务执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
