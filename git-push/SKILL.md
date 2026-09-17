---
name: git-push
description: 分析 git 未提交改动，按「新增/优化/修复Bug/移除」分类生成规范中文 commit message，提交并推送至 Gitee 远端。当用户说"推送"、"提交并推送"、"整理提交"、"git push"时使用。
---

# Git 规范提交与推送

将当前未提交的改动按类型分类，生成规范的中文 commit message，提交后推送到 Gitee 远端。

## 执行流程

### 1. 收集变更信息

并行执行以下命令，获取完整的变更信息：

```bash
git status
git diff --stat HEAD
git diff HEAD
git log --oneline -5
```

### 2. 分析并分类

逐文件分析 diff，将每个改动归入以下类型：

**新增** — 全新文件或功能：
- 新建的页面、组件、API 路由
- 新建的工具函数、类型定义
- Prisma/Schema 新增的模型或字段

**优化** — 对已有功能的改进：
- 重构简化代码（如减少行数、提取公共逻辑）
- UI/UX 改进（如自动选中、布局调整）
- 性能或可维护性提升
- 默认值/配置更新

**修复Bug** — 修复明确的问题：
- 运行时错误（500、404、类型错误等）
- 数据显示错误
- 功能逻辑缺陷
- API 参数缺失导致调用失败

**移除** — 删除的代码或功能：
- 移除不再使用的功能
- 删除冗余代码
- 下线旧逻辑

### 3. 生成 Commit Message

格式严格遵循：

```
feat: <简短摘要>

新增：
1. <描述>
2. <描述>

优化：
1. <描述>
2. <描述>

修复Bug：
1. <描述>

移除：
1. <描述>

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

规则：
- 摘要行保持 ~50 字以内，概括本次改动主题
- 每条描述一句话说清「改了什么 + 为什么/效果」
- 如果某类型无改动则省略
- 引用具体文件名帮助定位

### 4. 暂存文件

**唯一规则：`.gitignore` 已决定哪些文件不提交，除此之外全部提交。不做任何额外判断。**

```bash
git add -A
```

### 5. 提交并推送

```bash
git commit -m "$(cat <<'EOF'
<完整 message>
EOF
)"
git push origin master
```

## 注意事项

- **只信 `.gitignore`，不自行排除任何文件。** .gitignore 没忽略的统统提交
- 使用 HEREDOC 格式写 commit message，避免特殊字符转义问题
- 如果 commit 失败（如 pre-commit hook），修复问题后重新创建新 commit，不使用 --amend
- 每次提交后输出 commit SHA 和推送结果
