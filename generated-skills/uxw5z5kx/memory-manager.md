---
name: memory-manager
description: |
  帮助 agent 管理跨会话持久化记忆，存储和检索关键上下文信息。Triggers on: "记住", "记录下来", "下次记得", "我之前说过", "帮我记", "remember", "recall".
metadata:
  openclaw:
    emoji: "🧠"
---

# 记忆管理器

## 记忆存储规范

记忆文件存储在：`~/.claude/projects/<project-slug>/memory/`

### 记忆类型

| 类型 | 文件名前缀 | 用途 |
|------|-----------|------|
| `user` | `user_*.md` | 用户偏好、背景信息 |
| `project` | `project_*.md` | 项目上下文、进度 |
| `feedback` | `feedback_*.md` | 用户反馈和纠正 |
| `reference` | `reference_*.md` | 外部资源指针 |

### 写入记忆

每个记忆文件格式：
```markdown
---
name: 记忆名称
description: 一句话描述（用于决定相关性）
type: user | project | feedback | reference
---

记忆内容
```

同时更新 `MEMORY.md` 索引：
```markdown
- [记忆名称](./memory/文件名.md) — 简短描述
```

### 查询记忆

1. 先读取 `MEMORY.md` 获取索引
2. 根据相关性读取具体记忆文件
3. 不要读取所有记忆文件，按需加载

### 记忆更新原则

- **不重复**：先检查是否存在相似记忆再创建
- **不存代码**：代码模式不放记忆，放在代码本身
- **不存临时状态**：只存跨会话有价值的信息
- **及时更新**：发现记忆过期时立即更新或删除

### 触发时机

- 用户明确要求记住某事 → 立即写入
- 用户纠正你的行为 → 写入 feedback 类型记忆
- 发现用户有固定偏好 → 写入 user 类型记忆
