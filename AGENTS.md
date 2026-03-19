# RSS日报自动推送

## 项目概述
- **名称**: RSS日报自动推送
- **功能**: 从多个RSS源获取最新资讯，使用智谱AI生成结构化日报并推送到Telegram
- **架构**: GitHub Actions + Python脚本

## 技术栈
- **Python 3.10+**: 主要开发语言
- **智谱AI GLM-4-Flash**: 大语言模型（免费）
- **feedparser**: RSS解析
- **Telegram Bot API**: 消息推送
- **GitHub Actions**: 定时任务调度

## 项目结构

```
.
├── .github/workflows/
│   └── rss-daily.yml          # GitHub Actions定时任务
├── config/
│   └── generate_report_llm_cfg.json  # GLM模型配置
├── scripts/
│   ├── run_daily.py           # 主执行脚本
│   └── test_telegram.py       # Telegram配置测试
├── docs/                      # 文档
└── requirements.txt           # Python依赖
```

## RSS源列表

项目配置了22个RSS源：

**技术博客**
- Huli's blog: https://blog.huli.tw/feed.xml
- Platform Thinking: https://www.platformthinking.org/feed
- 1 Byte: https://1byte.io/feed.xml
- 阮一峰的网络日志: https://www.ruanyifeng.com/blog/atom.xml

**科技媒体**
- The Verge: https://www.theverge.com/rss/index.xml
- CSDN极客头条: https://www.csdn.net/rss/newest
- 少数派: https://sspai.com/feed
- HelloGitHub: https://hellogithub.com/rss

**中文资讯**
- 36氪: https://36kr.com/feed
- 知乎热榜: https://www.zhihu.com/rss
- 微博热榜: https://www.weibo.com/rss
- 财联社: https://www.cls.cn/rss

**加密货币**
- BlockBeats: https://www.theblockbeats.info/rss
- CryptoCat: https://cryptocat.world/rss
- 余烬: https://www.wublock123.com/rss

**社区热点**
- V2EX-Hot: https://www.v2ex.com/api/topics/hot.json
- Newlearner: https://www.newlearner.site/feed

**其他**
- 小赖子的英国生活和资讯: https://www.xiaolai.co/feed
- Chenyang Hsu: https://chenyang.co/feed
- 夏冰雹频道: https://summerice.top/feed
- 彭春花本人: https://pengchunhua.com/feed
- 橘鸦Juya: https://juyajuya.com/feed

## 配置说明

### 环境变量

| 变量名 | 必需 | 说明 |
|-------|------|------|
| `ZHIPUAI_API_KEY` | ✅ | 智谱AI API密钥 |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram机器人Token |
| `TELEGRAM_CHAT_ID` | ✅ | 接收消息的Chat ID |
| `HOURS_FILTER` | ❌ | 过滤最近N小时（默认24） |
| `TELEGRAM_API_BASE_URL` | ❌ | Telegram代理服务器（默认使用代理） |

### 模型配置

文件：`config/generate_report_llm_cfg.json`

```json
{
  "config": {
    "model": "glm-4-flash",  // 推荐：免费
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
```

可选模型：
- `glm-4-flash`: 免费 ✅
- `glm-4`: 0.1元/千tokens
- `glm-4-plus`: 0.5元/千tokens

## GitHub Actions配置

### Secrets配置

在GitHub仓库设置中添加：

1. `ZHIPUAI_API_KEY` - 智谱AI API Key
2. `TELEGRAM_BOT_TOKEN` - Telegram Bot Token
3. `TELEGRAM_CHAT_ID` - Telegram Chat ID

### 定时任务

- **触发时间**: 每天UTC 1:00（北京时间9:00）
- **配置文件**: `.github/workflows/rss-daily.yml`
- **支持手动触发**: 是

### 执行流程

```
1. Checkout代码
2. 安装Python 3.10
3. 安装依赖（requirements.txt + zhipuai）
4. 执行脚本 scripts/run_daily.py
   ├── 获取RSS文章
   ├── 过滤最近24小时
   ├── 调用智谱AI生成日报
   └── 推送到Telegram
```

## 本地开发

### 安装依赖

```bash
pip install -r requirements.txt
pip install zhipuai
```

### 运行测试

```bash
# 测试Telegram配置
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python scripts/test_telegram.py

# 运行完整流程
export ZHIPUAI_API_KEY="your_api_key"
python scripts/run_daily.py
```

## 消息格式

- **格式**: HTML（Telegram解析更稳定）
- **内容**: 
  - 📰 今日资讯概览
  - 🔥 热门推荐
  - 📚 分类资讯
  - 💡 今日亮点

详见：`docs/message_format.md`

## 费用说明

### 智谱AI
- GLM-4-Flash: **免费** ✅
- 新用户赠送免费tokens

### GitHub Actions
- 免费额度: 2,000分钟/月
- 本项目消耗: ~150-300分钟/月
- **完全免费** ✅

## 故障排查

### 常见问题

1. **智谱AI调用失败**
   - 检查API Key是否正确
   - 检查余额是否充足
   - 推荐使用GLM-4-Flash（免费）

2. **Telegram推送失败**
   - 检查Bot Token和Chat ID
   - 确认Bot有权限发送消息
   - 运行 `scripts/test_telegram.py` 测试

3. **无文章更新**
   - 增加 `HOURS_FILTER` 值
   - 检查RSS源是否正常

## 相关文档

- [快速开始](docs/quick_start.md)
- [GitHub Actions配置](docs/github_actions_setup.md)
- [Telegram配置教程](docs/telegram_setup.md)
- [消息格式说明](docs/message_format.md)
