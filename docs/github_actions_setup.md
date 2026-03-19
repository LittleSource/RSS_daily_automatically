# GitHub Actions 配置指南

## 配置步骤

### 1. Fork项目

点击仓库右上角的 `Fork` 按钮，将项目复制到你的账号下。

### 2. 配置Secrets

进入你的仓库：`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

**必需的Secrets：**

| Secret名称 | 说明 | 获取方式 |
|-----------|------|---------|
| `ZHIPUAI_API_KEY` | 智谱AI API密钥 | [智谱AI开放平台](https://open.bigmodel.cn/) |
| `TELEGRAM_BOT_TOKEN` | Telegram机器人Token | [Telegram配置教程](./telegram_setup.md) |
| `TELEGRAM_CHAT_ID` | 接收消息的Chat ID | [Telegram配置教程](./telegram_setup.md) |

**获取智谱AI API Key：**

1. 访问 https://open.bigmodel.cn/
2. 注册/登录账号
3. 进入「API密钥」页面
4. 点击「创建 API Key」
5. 保存生成的密钥

**免费额度：**
- ✅ 新用户赠送免费tokens
- ✅ GLM-4-Flash模型免费使用

### 3. 配置变量（可选）

在 `Variables` 标签页添加：

| 变量名称 | 默认值 | 说明 |
|---------|-------|------|
| `HOURS_FILTER` | `24` | 过滤最近N小时的文章 |

### 4. 启用Actions

1. 进入 `Actions` 标签页
2. 如果看到提示，点击 `I understand my workflows, go ahead and enable them`
3. 点击左侧的 `RSS Daily Report` 工作流
4. 点击右侧的 `Enable workflow`

### 5. 手动测试

1. 在 `RSS Daily Report` 页面
2. 点击右侧 `Run workflow` 按钮
3. 点击绿色的 `Run workflow` 确认
4. 等待执行完成，查看日志

## 定时任务配置

### 默认时间

每天 **UTC 1:00**（北京时间 **9:00**）自动执行

### 修改时间

编辑 `.github/workflows/rss-daily.yml`：

```yaml
on:
  schedule:
    - cron: '0 1 * * *'  # UTC时间1:00
```

### Cron表达式说明

```
┌───────────── 分钟 (0 - 59)
│ ┌───────────── 小时 (0 - 23)
│ │ ┌───────────── 日期 (1 - 31)
│ │ │ ┌───────────── 月份 (1 - 12)
│ │ │ │ ┌───────────── 星期 (0 - 6) (0是周日)
│ │ │ │ │
* * * * *
```

**常用示例：**

| 表达式 | 说明 |
|-------|------|
| `0 1 * * *` | 每天 UTC 1:00（北京9:00） |
| `0 17 * * *` | 每天 UTC 17:00（北京凌晨1:00） |
| `0 */6 * * *` | 每6小时一次 |
| `0 9 * * 1-5` | 周一到周五 UTC 9:00（北京17:00） |

**注意**：GitHub Actions使用UTC时间，北京时间需要减8小时

## 查看执行日志

1. 进入 `Actions` 标签页
2. 点击具体的workflow运行记录
3. 展开 `Run RSS Daily Report` 步骤
4. 查看详细日志

### 成功日志示例

```
🚀 开始执行RSS日报推送...
开始获取RSS源，过滤最近24小时的文章...
获取: https://blog.huli.tw/feed.xml
获取: https://www.theverge.com/rss/index.xml
...
获取完成，共45篇文章
开始调用智谱AI生成日报...
日报生成成功
开始发送到Telegram...
✅ Telegram推送成功
==================================================
✅ RSS日报推送成功！
📊 文章数: 45
💬 消息ID: 12345
==================================================
```

## 故障排查

### Actions失败

**检查清单：**

1. **Secrets配置错误**
   ```
   ❌ 缺少智谱AI API Key：请设置 ZHIPUAI_API_KEY 环境变量
   ```
   → 重新配置Secrets，确保名称完全一致

2. **智谱AI调用失败**
   ```
   ❌ 调用智谱AI失败: API key is invalid
   ```
   → 检查API Key是否正确，是否已过期

3. **Telegram配置错误**
   ```
   ❌ 缺少Telegram配置：请设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 环境变量
   ```
   → 重新配置Telegram Secrets

4. **Chat ID错误**
   ```
   ❌ Telegram推送失败: Bad Request: chat not found
   ```
   → 确认Chat ID正确，参考 [Telegram配置教程](./telegram_setup.md)

### 本地测试

```bash
# 1. 安装依赖
pip install -r requirements.txt
pip install zhipuai

# 2. 设置环境变量
export ZHIPUAI_API_KEY="your_api_key"
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export HOURS_FILTER="24"

# 3. 运行脚本
python scripts/run_daily.py
```

### 调试模式

在脚本中添加更多日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)  # 改为DEBUG级别
```

## 费用说明

### 智谱AI费用

| 模型 | 价格 | 推荐 |
|------|------|------|
| GLM-4-Flash | 免费 | ✅ 推荐 |
| GLM-4 | 0.1元/千tokens | 高质量场景 |
| GLM-4-Plus | 0.5元/千tokens | 专业场景 |

**免费额度：**
- 新用户赠送免费tokens
- GLM-4-Flash完全免费

### GitHub Actions费用

| 账号类型 | 免费分钟数/月 | 存储空间 |
|---------|-------------|---------|
| GitHub Free | 2,000分钟 | 500MB |
| GitHub Pro | 3,000分钟 | 1GB |

**本项目消耗：**
- 每次执行约 5-10 分钟
- 每月约 150-300 分钟
- 完全在免费额度内 ✅

## 高级配置

### 多时间点推送

修改 `.github/workflows/rss-daily.yml`：

```yaml
schedule:
  - cron: '0 1 * * *'   # 北京9:00
  - cron: '0 7 * * *'   # 北京15:00
  - cron: '0 13 * * *'  # 北京21:00
```

### 条件执行

仅在特定分支执行：

```yaml
jobs:
  generate-and-push:
    if: github.ref == 'refs/heads/main'
```

### 失败通知

添加失败通知到Telegram：

```yaml
- name: Notify on Failure
  if: failure()
  run: |
    curl -X POST "https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage" \
      -d "chat_id=${{ secrets.TELEGRAM_CHAT_ID }}" \
      -d "text=❌ RSS日报推送失败，请检查GitHub Actions日志"
```

## 相关文档

- [快速开始](./quick_start.md)
- [Telegram配置教程](./telegram_setup.md)
