# 龙虾学校 TODO

## 已完成
- [x] 域名切换：`school.teamolab.com` → `clawschool.teamolab.com`（ICP 拦截问题）
- [x] 服务器切换：上海 49.234.52.43 → 香港 101.32.218.111（`lhins-qvamlqej`）
- [x] SKILL.md 大小写修复（nginx 配置要求大写 SKILL.md）

## 待办

### SKILL.md 升级 (PGT v1)
- [ ] 审核 `龙虾学校测试题/SKILL.md` (PGT 改版)，决定是否采用
  - 新版题目顺序和内容完全不同
  - 新版 summary.json 格式不兼容现有 scorer.py（缺少 token/lobster_name，字段结构不同）
  - 如采用需同步重写 scorer.py
