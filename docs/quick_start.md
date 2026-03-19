# 快速开始指南

## 三步配置

### 第一步：Fork项目

点击右上角 `Fork` 按钮

### 第二步：获取API密钥

#### 2.1 智谱AI API Key

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册/登录账号
3. 进入「API密钥」页面
4. 创建新的API Key
5. 保存API Key（格式：`xxx.xxx`）

**免费额度：**
- 新用户赠送免费tokens
- GLM-4-Flash模型免费使用

#### 2.2 Telegram配置

**创建Telegram Bot：**
1. 在Telegram搜索 `@BotFather`
2. 发送 `/newbot`
3. 按提示设置Bot名称
4. 保存返回的 **Bot Token**（格式：`123456789:ABCdef...`）

**获取Chat ID：**

*个人聊天：*
1. 在Telegram搜索 `@userinfobot`
2. 发送任意消息
3. 获取返回的 **ID**（数字）

*群组聊天：*
1. 将Bot添加到群组
2. 发送一条消息
3. 访问 `https://api.telegram.org/bot<YourBOTToken>/getUpdates`
4. 找到 `"chat":{"id":<ChatID>`

#### 2.3 测试配置

```bash
# 安装依赖
pip install requests

# 设置环境变量
export TELEGRAM_BOT_TOKEN="123456789:ABCdef..."
export TELEGRAM_CHAT_ID="123456789"

# 运行测试
python scripts/test_telegram.py
```

看到 `✅ 测试成功！` 即表示Telegram配置正确

### 第三步：配置GitHub Secrets

1. 进入Fork的仓库
2. `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`

添加三个Secret：

| Name | Value | 说明 |
|------|-------|------|
| `ZHIPUAI_API_KEY` | 你的智谱AI API Key | 用于调用GLM模型 |
| `TELEGRAM_BOT_TOKEN` | 你的Bot Token | Telegram机器人 |
| `TELEGRAM_CHAT_ID` | 你的Chat ID | 接收消息的聊天 |

## 启用定时任务

### 启用Actions

1. 进入 `Actions` 标签页
2. 点击 `I understand my workflows, go ahead and enable them`
3. 点击左侧 `RSS Daily Report`
4. 点击 `Enable workflow`

### 手动测试

1. 点击右侧 `Run workflow`
2. 点击绿色 `Run workflow` 按钮
3. 等待执行完成

### 查看结果

在Telegram中查看推送的日报消息

## 自定义配置

### 修改推送时间

编辑 `.github/workflows/rss-daily.yml`：

```yaml
schedule:
  - cron: '0 1 * * *'  # UTC时间，北京时间需要+8
```

常用时间：

| 北京时间 | UTC时间 | Cron表达式 |
|---------|--------|-----------|
| 9:00 | 1:00 | `0 1 * * *` |
| 12:00 | 4:00 | `0 4 * * *` |
| 18:00 | 10:00 | `0 10 * * *` |
| 21:00 | 13:00 | `0 13 * * *` |

### 修改RSS源

编辑 `scripts/run_daily.py`，修改 `RSS_SOURCES` 列表：

```python
RSS_SOURCES = [
    "https://your-rss-url.com/feed",
    # 添加更多RSS源...
]
```

### 修改过滤时间

在GitHub Variables中设置 `HOURS_FILTER`：

- 默认：24小时
- 可选：12小时、48小时等

### 自定义日报风格

编辑 `config/generate_report_llm_cfg.json`：

```json
{
  "sp": "你的自定义系统提示词...",
  "config": {
    "model": "glm-4-flash",  // 可选: glm-4, glm-4-plus
    "temperature": 0.7  // 调整创造性（0-1）
  }
}
```

## 本地运行

```bash
# 1. 克隆项目
git clone https://github.com/your-username/your-repo.git
cd your-repo

# 2. 安装依赖
pip install -r requirements.txt
pip install zhipuai

# 3. 设置环境变量
export ZHIPUAI_API_KEY="your_api_key"
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export HOURS_FILTER="24"

# 4. 运行
python scripts/run_daily.py
```

## 故障排查

### 问题：智谱AI调用失败

**原因：** API Key无效或余额不足

**解决：**
1. 检查API Key是否正确
2. 登录智谱AI控制台查看余额
3. 使用GLM-4-Flash模型（免费）

### 问题：Telegram推送失败

**原因：** Bot Token 或 Chat ID 错误

**解决：**
1. 重新获取Token和Chat ID
2. 运行 `python scripts/test_telegram.py` 验证

### 问题：GitHub Actions失败

**原因：** Secrets配置错误

**解决：**
1. 检查Secrets名称是否完全一致（区分大小写）
2. 检查所有三个Secret是否都已配置
3. 查看Actions日志了解详细错误

### 问题：无文章更新

**原因：** 时间范围内无新文章

**解决：**
1. 增加 `HOURS_FILTER` 值
2. 检查RSS源是否正常

## 下一步

- 📖 查看 [GitHub Actions详细配置](./github_actions_setup.md)
- 📖 查看 [Telegram配置教程](./telegram_setup.md)
- 📖 查看 [消息格式说明](./message_format.md)

## 费用说明

### 智谱AI

| 项目 | 说明 |
|------|------|
| 新用户 | 赠送免费tokens |
| GLM-4-Flash | 免费 ✅ |
| GLM-4 | 按量计费 |
| GLM-4-Plus | 按量计费 |

**推荐使用 GLM-4-Flash，完全免费！**

### GitHub Actions

| 账号类型 | 免费分钟数/月 | 存储空间 |
|---------|-------------|---------|
| GitHub Free | 2,000分钟 | 500MB |
| GitHub Pro | 3,000分钟 | 1GB |

**本项目消耗：**
- 每次执行约 5-10 分钟
- 每月约 150-300 分钟
- 完全在免费额度内 ✅

## 需要帮助？

遇到问题？查看 [GitHub Issues](https://github.com/your-username/your-repo/issues)
