# HTTP无响应问题修复指南

## 问题原因

RSS日报生成工作流需要约**6分钟**执行时间，但HTTP请求默认会在短时间后超时，导致"无响应"现象。

## 已实施的修复

### 1. 异步API支持

已在 `src/main.py` 中添加异步模式支持：

- **异步模式**：立即返回任务ID，后台执行工作流
- **状态查询接口**：通过 `/status/{run_id}` 查询执行状态和结果

### 2. 新增API接口

#### 启动异步任务
```bash
POST /run?async=true
```

#### 查询任务状态
```bash
GET /status/{run_id}
```

## 部署步骤

### 步骤1：重启服务

代码已更新，需要重启服务以加载新功能：

```bash
# 找到当前运行的进程
ps aux | grep "python.*main.py"

# 停止旧服务（替换PID为实际进程ID）
kill <PID>

# 启动新服务
cd /workspace/projects
nohup python src/main.py -m http -p 5000 > /var/log/rss_service.log 2>&1 &
```

### 步骤2：测试异步API

```bash
# 启动异步任务
curl -X POST "http://localhost:5000/run?async=true" \
  -H "Content-Type: application/json" \
  -d '{"hours_filter": 24}'
```

预期立即返回：
```json
{
  "status": "accepted",
  "run_id": "xxxx-xxxx-xxxx",
  "message": "Task started. Use /status/{run_id} to check progress."
}
```

### 步骤3：查询任务状态

```bash
# 使用返回的run_id查询
curl -X GET "http://localhost:5000/status/xxxx-xxxx-xxxx"
```

## 使用建议

### 1. 使用异步模式（强烈推荐）

所有请求都加上 `?async=true` 参数：

```bash
curl -X POST "http://your-domain:5000/run?async=true" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 2. 配置Telegram环境变量

在启动服务前设置：

```bash
export TELEGRAM_BOT_TOKEN="你的Bot Token"
export TELEGRAM_CHAT_ID="你的Chat ID"
```

### 3. 设置定时任务

```bash
# 编辑crontab
crontab -e

# 每天早上9点执行
0 9 * * * curl -X POST "http://localhost:5000/run?async=true" -H "Content-Type: application/json" -d '{}'
```

## 同步模式使用（不推荐）

如果必须使用同步模式，需要设置HTTP客户端超时至少10分钟：

```bash
# 使用curl的--max-time参数
curl -X POST "http://localhost:5000/run" \
  -H "Content-Type: application/json" \
  -d '{}' \
  --max-time 600
```

## 完整API文档

详细API使用说明请参考：`docs/api_usage.md`

## 故障排查

### 检查服务状态
```bash
ps aux | grep "python.*main.py"
netstat -tlnp | grep 5000
```

### 查看日志
```bash
tail -f /app/work/logs/bypass/app.log
```

### 测试工作流
```bash
# 使用test_run测试工作流本身
python -c "from graphs.graph import main_graph; print('OK')"
```

## 重启服务命令（完整）

```bash
# 1. 停止旧服务
pkill -f "python.*main.py.*http"

# 2. 设置环境变量
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# 3. 启动新服务
cd /workspace/projects
nohup python src/main.py -m http -p 5000 > /var/log/rss_service.log 2>&1 &

# 4. 检查服务是否启动
sleep 3
curl http://localhost:5000/status/test
```

## 注意事项

1. **必须重启服务**才能使用新的异步API功能
2. 异步模式需要客户端轮询查询状态
3. 任务结果会在查询时返回
4. 建议使用定时任务而不是手动触发
