# 定时任务配置检查报告

## 检查结果

### ❌ 问题发现

1. **服务启动时间**：10:49:15（今天早上8:30服务未运行）
2. **定时任务**：未配置自动定时执行
3. **推送记录**：日志中无推送记录

### 🔍 原因分析

- 服务在10:49才启动，错过了早上8:30的推送时间
- 没有配置定时任务来自动触发RSS日报生成
- 需要手动调用或配置定时任务

## 解决方案

### 方案一：使用APScheduler（推荐）

在服务内部添加定时任务，服务启动后自动执行。

#### 实现步骤

1. **安装依赖**（已安装）
```bash
pip install apscheduler
```

2. **修改 main.py**，添加定时任务

在 `src/main.py` 中添加：

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

# 创建调度器
scheduler = AsyncIOScheduler()

async def scheduled_rss_report():
    """定时任务：每天8:30执行RSS日报"""
    logger.info("Starting scheduled RSS report task at 8:30 AM")
    try:
        # 创建空的payload
        payload = {}
        # 创建上下文
        ctx = new_context(method="scheduled_task")
        # 执行工作流
        result = await service.run(payload, ctx)
        logger.info(f"Scheduled task completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled task failed: {e}", exc_info=True)

# 在应用启动时添加定时任务
@app.on_event("startup")
async def startup_event():
    # 添加每天8:30执行的任务
    scheduler.add_job(
        scheduled_rss_report,
        CronTrigger(hour=8, minute=30),
        id="rss_daily_report",
        name="RSS Daily Report at 8:30 AM",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started, daily report scheduled at 8:30 AM")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler shutdown")
```

### 方案二：使用systemd timer

创建系统级定时任务。

#### 步骤

1. 创建服务文件 `/etc/systemd/system/rss-daily.service`:
```ini
[Unit]
Description=RSS Daily Report Generator
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/workspace/projects
Environment="TELEGRAM_BOT_TOKEN=你的Bot Token"
Environment="TELEGRAM_CHAT_ID=你的Chat ID"
ExecStart=/usr/bin/curl -X POST http://localhost:5000/run?async=true -H "Content-Type: application/json" -d '{}'

[Install]
WantedBy=multi-user.target
```

2. 创建定时器文件 `/etc/systemd/system/rss-daily.timer`:
```ini
[Unit]
Description=Run RSS Daily Report at 8:30 AM

[Timer]
OnCalendar=*-*-* 08:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

3. 启用定时器：
```bash
systemctl daemon-reload
systemctl enable rss-daily.timer
systemctl start rss-daily.timer
```

### 方案三：使用crontab

如果系统有crontab，可以配置：

```bash
# 安装crontab（如果没有）
apt-get install -y cron

# 编辑crontab
crontab -e

# 添加以下行（每天8:30执行）
30 8 * * * cd /workspace/projects && curl -X POST http://localhost:5000/run?async=true -H "Content-Type: application/json" -d '{}' >> /var/log/rss_daily.log 2>&1
```

## 当前状态

- ✅ 服务正常运行（端口5000）
- ✅ 工作流功能完整
- ❌ 未配置定时任务
- ❌ Telegram环境变量未配置

## 立即执行

如果需要立即执行一次推送：

```bash
curl -X POST "http://localhost:5000/run?async=true" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 建议

**推荐使用方案一（APScheduler）**：
- ✅ 集成在服务内部，无需外部配置
- ✅ 服务启动后自动运行
- ✅ 日志统一管理
- ✅ 易于监控和调试

需要我帮你实现哪个方案？
