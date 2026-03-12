---
name: code-debug-helper
description: |
  当代码执行失败或出现异常时，提供系统化调试流程和错误分析。Triggers on: "报错", "出错了", "debug", "调试", "执行失败", "error", "exception", "traceback".
metadata:
  openclaw:
    emoji: "🐛"
---

# 代码调试助手

## 调试标准流程

### 第一步：收集错误信息

```bash
# 捕获完整错误输出
<命令> 2>&1 | tee /tmp/debug_output.txt

# 查看最近的错误日志
tail -50 /tmp/debug_output.txt
```

### 第二步：错误分类

| 错误类型 | 特征 | 优先检查 |
|---------|------|--------|
| 语法错误 | SyntaxError, ParseError | 检查括号、缩进、引号 |
| 运行时错误 | RuntimeError, TypeError | 检查变量类型和值 |
| 依赖错误 | ModuleNotFoundError, ImportError | 检查包安装和路径 |
| 权限错误 | PermissionError, EACCES | 检查文件/目录权限 |
| 网络错误 | ConnectionError, TimeoutError | 检查网络和端点 |

### 第三步：最小复现

1. 隔离出最小能复现问题的代码片段
2. 确认是否是环境问题（在其他环境是否复现）
3. 检查最近的代码变更是否引入问题

### 第四步：修复验证

```bash
# 修复后运行测试
<测试命令>

# 确认错误消失
echo "退出码: $?"
```

## 常见问题速查

### Python
```bash
# 检查依赖
pip list | grep <包名>
# 检查语法
python -m py_compile <文件>.py
# 详细错误
python -v <文件>.py
```

### Node.js
```bash
# 检查依赖
ls node_modules/<包名>
# 检查语法
node --check <文件>.js
```

### Shell 脚本
```bash
# 调试模式
bash -x <脚本>.sh
# 语法检查
bash -n <脚本>.sh
```

## 安全调试原则

- 不在生产环境直接调试，先在测试环境复现
- 不输出敏感变量（密码、API Key）到日志
- 调试完成后清理临时日志文件
