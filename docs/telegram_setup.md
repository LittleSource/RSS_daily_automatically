# Telegram Bot 配置指南

## 快速开始

### 第一步：创建 Telegram Bot

1. 在 Telegram 中搜索 `@BotFather`
2. 发送命令 `/newbot`
3. 按提示输入 Bot 名称和用户名
4. 保存返回的 **Bot Token**（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 第二步：获取 Chat ID

#### 方法一：个人聊天
1. 在 Telegram 中搜索 `@userinfobot`
2. 发送任意消息，它会返回你的 **User ID**（这就是 Chat ID）

#### 方法二：群组聊天
1. 将你的 Bot 添加到群组
2. 在群组中发送消息
3. 访问以下 URL（替换 `{bot_token}` 和 `{group_username}`）：
   ```
   http://f.52ym.vip/telegram/bot{bot_token}/getChat?chat_id=@{group_username}
   ```
4. 返回的 JSON 中的 `result.id` 就是 Chat ID

#### 方法三：使用 API 获取
访问以下 URL 获取最近的更新：
```
http://f.52ym.vip/telegram/bot{bot_token}/getUpdates
```
从中找到 `chat.id` 字段

### 第三步：配置环境变量

在你的运行环境中设置以下环境变量：

```bash
export TELEGRAM_BOT_TOKEN="你的Bot Token"
export TELEGRAM_CHAT_ID="你的Chat ID"
```

或者在 `src/main.py` 中添加：
```python
import os
os.environ["TELEGRAM_BOT_TOKEN"] = "你的Bot Token"
os.environ["TELEGRAM_CHAT_ID"] = "你的Chat ID"
```

### 第四步：自定义API服务器（可选）

默认使用代理服务器：`http://f.52ym.vip/telegram`

如需使用其他服务器，可配置环境变量：
```bash
export TELEGRAM_API_BASE_URL="http://f.52ym.vip/telegram"
```

如需使用官方API（需科学上网）：
```bash
export TELEGRAM_API_BASE_URL="https://api.telegram.org"
```

## 消息格式

工作流会以 Markdown 格式发送日报，包含：
- 标题和分类
- 文章链接（可点击）
- 简洁摘要
- 自动分页（超过4096字符时）

## 测试推送

配置完成后，运行工作流即可自动推送日报到 Telegram。

## 常见问题

### Bot 没有权限发送消息
- 确保 Bot 已被添加到目标群组
- 确保群组中有至少一条消息
- 确保 Chat ID 正确（群组 Chat ID 通常为负数）

### 找不到 Chat ID
- 使用 `@userinfobot` 获取个人 ID
- 使用 API `getUpdates` 方法获取最新消息中的 Chat ID

### 消息发送失败
- 检查 Bot Token 是否正确
- 检查 Chat ID 是否正确
- 检查网络连接是否正常
- 检查自定义API服务器是否可访问

### 使用代理服务器
本工作流默认使用代理服务器 `http://f.52ym.vip/telegram`，无需科学上网即可推送消息。
