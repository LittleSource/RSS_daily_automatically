# Discord 配置指南

项目现在支持把日报推送到 Discord。

## 方式一：Webhook

这是最简单的接入方式，推荐优先使用。

1. 打开 Discord 频道设置。
2. 进入 `Integrations` -> `Webhooks`。
3. 创建一个新的 Webhook。
4. 复制 Webhook URL。
5. 配置环境变量：

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

GitHub Actions 中请将它配置为仓库 Secret：

- `DISCORD_WEBHOOK_URL`

## 方式二：Bot Token + Channel ID

如果你希望使用标准 Discord Bot，也可以使用下面这组配置：

```bash
export DISCORD_BOT_TOKEN="your_discord_bot_token"
export DISCORD_CHANNEL_ID="your_channel_id"
```

GitHub Actions 中请配置以下 Secrets：

- `DISCORD_BOT_TOKEN`
- `DISCORD_CHANNEL_ID`

Bot 需要具备目标频道的发言权限。

## 本地测试

Webhook 方式：

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python scripts/test_discord.py
```

Bot 方式：

```bash
export DISCORD_BOT_TOKEN="your_discord_bot_token"
export DISCORD_CHANNEL_ID="your_channel_id"
python scripts/test_discord.py
```

## 说明

- 如果同时配置了 `DISCORD_WEBHOOK_URL` 和 Bot Token，脚本会优先使用 Webhook。
- Telegram 和 Discord 可以同时启用，日报会并行发送到所有已配置通道。
