# RSS日报自动推送

从多个RSS源获取最新资讯，生成结构化日报并推送到Telegram。

## 🎯 特性

- ✅ **多源聚合**：支持22个RSS源并发获取
- ✅ **智能过滤**：自动过滤最近N小时的内容
- ✅ **AI生成**：使用智谱AI GLM模型生成结构化日报
- ✅ **自动推送**：定时推送到Telegram
- ✅ **零成本**：基于GitHub Actions + GLM-4-Flash，完全免费

## 🚀 快速开始

### 1. Fork本项目

点击右上角 `Fork` 按钮

### 2. 获取API密钥

#### 智谱AI API Key

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册/登录账号
3. 进入「API密钥」页面创建API Key
4. **GLM-4-Flash模型免费使用** ✅

#### Telegram配置

1. 在Telegram搜索 `@BotFather`，发送 `/newbot` 创建机器人
2. 搜索 `@userinfobot` 获取Chat ID
3. 详细教程：[Telegram配置教程](docs/telegram_setup.md)

### 3. 配置GitHub Secrets

进入仓库 `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Secret名称 | 说明 |
|-----------|------|
| `ZHIPUAI_API_KEY` | 智谱AI API Key |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | 接收消息的Chat ID |

### 4. 启用GitHub Actions

进入 `Actions` 标签页，启用工作流，手动触发测试

## 📅 定时任务

每天 **UTC 1:00**（北京时间 **9:00**）自动执行

修改时间：编辑 `.github/workflows/rss-daily.yml` 中的 cron 表达式

## 🔧 本地运行

### 安装依赖

```bash
pip install -r requirements.txt
pip install zhipuai
```

### 设置环境变量

```bash
export ZHIPUAI_API_KEY="your_api_key"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export HOURS_FILTER="24"  # 可选
```

### 运行脚本

```bash
python scripts/run_daily.py
```

### 测试Telegram配置

```bash
python scripts/test_telegram.py
```

## 📁 项目结构

```
.
├── .github/
│   └── workflows/
│       └── rss-daily.yml      # GitHub Actions配置
├── config/
│   └── generate_report_llm_cfg.json  # GLM模型配置
├── scripts/
│   ├── run_daily.py           # 主执行脚本
│   └── test_telegram.py       # Telegram配置测试
├── docs/                      # 文档
└── requirements.txt           # Python依赖
```

## 🔍 工作流程

```
GitHub Actions (定时触发)
    ↓
Python脚本执行
    ↓
RSS获取 (22个源并发)
    ↓
内容过滤 (最近24小时)
    ↓
智谱AI生成日报
    ↓
Telegram推送
```

## 📖 RSS源列表

项目配置了22个优质RSS源：

<details>
<summary>点击查看完整列表</summary>

### 技术博客
- Huli's blog
- Platform Thinking
- 1 Byte
- 阮一峰的网络日志

### 科技媒体
- The Verge
- CSDN极客头条
- 少数派
- HelloGitHub

### 中文资讯
- 36氪
- 知乎热榜
- 微博热榜
- 财联社

### 加密货币
- BlockBeats
- CryptoCat | 猫姐
- 余烬

### 社区热点
- V2EX-Hot
- Newlearnerの自留地

### 其他
- 小赖子的英国生活和资讯
- Chenyang Hsu
- 夏冰雹频道
- 彭春花本人
- 橘鸦Juya

</details>

## 📝 消息格式

推送的消息采用HTML格式，**文章标题是可点击的超链接**：

```
📰 今日资讯日报
📅 2024年03月19日 | 📊 共45篇资讯

🔥 热门推荐

1️⃣ 【推荐】美国财政部今日将执行历史最大规模回购
摘要：美国财政部预计今天将回购150亿美元...

📚 分类资讯

【BlockBeats】
• 花旗银行估算香港稳定币市场规模约1248亿港元
  摘要：花旗预计香港稳定币规模约1248亿港元...
```

**特点**：
- 📰 文章标题可点击跳转（不显示冗长URL）
- 📊 清晰的分类结构
- 💡 今日亮点总结

## 🛠️ 自定义配置

### 修改RSS源

编辑 `scripts/run_daily.py` 中的 `RSS_SOURCES` 列表

### 修改日报风格

编辑 `config/generate_report_llm_cfg.json`：

```json
{
  "config": {
    "model": "glm-4-flash",  // 可选: glm-4, glm-4-plus
    "temperature": 0.7
  },
  "sp": "你的自定义系统提示词..."
}
```

### 修改推送时间

编辑 `.github/workflows/rss-daily.yml` 中的 cron 表达式

## 💰 费用说明

### 智谱AI

| 模型 | 价格 |
|------|------|
| GLM-4-Flash | **免费** ✅ |
| GLM-4 | 0.1元/千tokens |
| GLM-4-Plus | 0.5元/千tokens |

### GitHub Actions

| 账号类型 | 免费分钟数/月 |
|---------|-------------|
| GitHub Free | 2,000分钟 |
| GitHub Pro | 3,000分钟 |

**本项目消耗**：约150-300分钟/月，完全免费 ✅

## 📚 文档

- [快速开始](docs/quick_start.md)
- [Telegram配置教程](docs/telegram_setup.md)
- [GitHub Actions配置](docs/github_actions_setup.md)
- [消息格式说明](docs/message_format.md)

## ❓ 常见问题

<details>
<summary>智谱AI调用失败？</summary>

1. 检查API Key是否正确
2. 登录智谱AI控制台查看余额
3. 推荐使用GLM-4-Flash（免费）

</details>

<details>
<summary>GitHub Actions执行失败？</summary>

1. 检查Secrets是否正确配置（3个Secret）
2. 查看Actions日志了解具体错误
3. 本地测试验证配置

</details>

<details>
<summary>Telegram推送失败？</summary>

1. 确认Bot Token正确
2. 确认Chat ID正确（不是用户名）
3. 确认Bot有权限发送消息到该Chat
4. 运行 `python scripts/test_telegram.py` 测试

</details>

## 📄 License

MIT
