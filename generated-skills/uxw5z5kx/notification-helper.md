---
name: notification-helper
description: |
  当用户需要发送提醒、通知或告警时提供多渠道通知方案。Triggers on: "提醒我", "发送通知", "告警", "notify", "提醒", "send alert".
metadata:
  openclaw:
    emoji: "🔔"
---

# 通知渠道助手

## 使用说明

当需要发送通知或提醒时，按以下优先级选择渠道：

### 渠道优先级

1. **系统通知**（桌面环境可用时）
   ```bash
   # macOS
   osascript -e 'display notification "消息内容" with title "标题"'
   # Linux (需要 notify-send)
   notify-send "标题" "消息内容"
   ```

2. **文件写入通知**（通用方案，始终可用）
   ```bash
   echo "[$(date)] 通知：<消息内容>" >> ~/Desktop/notifications.log
   ```

3. **Gmail 草稿**（需要 Gmail MCP 工具）
   - 使用 `gmail_create_draft` 工具创建邮件草稿
   - 适合需要正式记录的通知

### 决策流程

```
用户请求通知
    ↓
检查是否有 osascript/notify-send → 是 → 发送系统通知
    ↓ 否
检查是否有 Gmail MCP → 是 → 创建邮件草稿
    ↓ 否
写入本地通知文件（~/Desktop/notifications.log）
```

### 注意事项
- 始终告知用户实际使用了哪个渠道
- 如果所有渠道都不可用，明确告知用户并建议配置
- 不要静默失败，必须给出明确反馈
