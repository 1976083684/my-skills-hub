---
name: mianshiya-problem-pull-ver2-tixi
description: 爬取面试鸭题库，按技术体系路线（而非难度）分类整理成 Markdown 复习清单。当用户提供 mianshiya.com/bank/<id> 链接并说"爬取面试鸭""导出面试题""按知识体系分类""按技术体系整理""归类整理""保存复习清单"时使用。与旧版 pull-mianshiya-problem（按难度输出表格）不同，本技能输出按知识体系分组的标题式清单，每类内由简到难排序。只要是"要把面试题按体系分类整理"的诉求，都应使用本技能，即使没明确说出"体系"二字。
---

# 面试鸭题目体系分类整理

从面试鸭题库拉取全部题目，按该技术领域的**知识体系路线**（而非难度）分类，生成便于按体系复习的 Markdown 清单。

## 核心区别：与旧版按难度分类不同

旧版 `pull-mianshiya-problem` 按 简单/中等/困难 三档输出表格。本版按技术体系分组，输出标题式列表：

- 分类标题：`### ✅索引（14道）`
- 题目：`#### [MySQL 的索引类型有哪些？](url)  - 简单`
- 每类内按难度排序（简单 → 中等 → 困难）

## 工作流程

### 1. 获取题库链接

从用户消息中提取面试鸭题库 URL 中的 `bank_id`（`https://www.mianshiya.com/bank/<bank_id>`）。

### 2. 确定输出目录

用户指定则直接用；否则询问。个人笔记仓库里通常是对应专题目录（如 `面试突击/1.数据库调优`）。

### 3. 爬取题目数据

```bash
pip install requests -q 2>&1 | tail -1
python <skill-path>/scripts/scrape.py "<bank_url>" "<output_dir>"
```

生成 `<主题名>·题目数据.json`，含全部题目的 `id / title / difficulty / url`。读取它，作为分类的依据。

### 4. 设计技术体系分类（关键步骤）

分类必须体现该技术领域的**体系路线**，而非凭感觉分。反例：`DELETE/DROP/TRUNCATE 的区别` 属于 **SQL 基础命令**，不是 SQL 优化；`EXPLAIN / 慢SQL / 分页优化` 才是 **SQL 优化**。

具体做法：

1. **先看项目里的技术体系**：若笔记仓库有该主题的笔记目录（如 `1.全面理解Mysql架构`、`2.深入理解Mysql索引`、`5.深入理解Mysql事务隔离级别与锁机制`...），优先以这些笔记主题作为体系分类的蓝本——它们代表用户自己的学习/复习路线。
2. **补齐体系缺口**：参考该技术公认的学习路线，补上笔记未覆盖的部分（如"SQL 基础命令"）。
3. **设计 8-12 个分类**，分类名简洁（2-6 字），顺序体现从基础到进阶的路线。
4. **每道题只归一类，归属要准确**：题目问"什么"就归"哪个体系"。注意拆解容易混淆的主题：事务、锁、MVCC 是三个独立体系，即使紧密相关也不合并；存储引擎（Buffer Pool/Change Buffer/Doublewrite）与日志（redo/undo/binlog/WAL）可各自独立或按笔记合并，但归属必须自洽。
5. 面试应用题（"你在项目中如何..."）归「实战场景」类。

### 5. 生成 Markdown

用 Python 脚本生成（避免手工写上百行易出错）。只需确定 `CAT`（题目 id → 分类名）和 `ORDER`（分类顺序）两个映射，套用下方模板。生成后**校验题目总数**（各类题数之和 = JSON 中总题数），防止遗漏或重复。

### 6. 清理临时文件

删除临时分类脚本。询问用户是否需要删除 JSON 数据文件（用户可能想保留用于后续重分类）。

## 输出格式

文件名：`<主题名>·知识体系清单.md`

```markdown
# MySQL 面试题·知识体系清单

> 来源：面试鸭 | 共 82 道题 | 按 MySQL 技术体系路线分类，每类内由简到难排序

### ✅索引与 B+ 树（14道）

#### [MySQL 的索引类型有哪些？](https://www.mianshiya.com/bank/1791003439968264194/question/1780933295438065665)  - 简单

#### [MySQL 中的回表是什么？](https://www.mianshiya.com/bank/1791003439968264194/question/1780933295446454273)  - 中等
```

- 分类标题：`### ✅<分类名>（<N>道）`
- 每题：`#### [<题目>](<url>)  - <难度>`（链接前后各一个空格 + 连字符）
- 每类内按难度排序：简单 → 中等 → 困难

## 生成脚本模板

```python
# -*- coding: utf-8 -*-
import json

BASE = "<输出目录>"
with open(f"{BASE}/<主题名>·题目数据.json", encoding="utf-8") as f:
    questions = json.load(f)

# 每道题按 id 归属的技术体系分类
CAT = {
    "<题目id>": "<分类名>",
    # ...
}

# 分类顺序 = 技术体系路线，从基础到进阶
ORDER = ["<分类1>", "<分类2>", ...]
DIFF_ORDER = {"简单": 0, "中等": 1, "困难": 2}

groups = {c: [] for c in ORDER}
for q in questions:
    cat = CAT[q["id"]]          # 确保每道题都有归属
    groups[cat].append(q)

for c in ORDER:
    groups[c].sort(key=lambda q: DIFF_ORDER[q["difficulty"]])

lines = ["# <主题名>·知识体系清单", "",
         "> 来源：面试鸭 | 共 {} 道题 | 按技术体系路线分类，每类内由简到难排序".format(len(questions)), ""]
for c in ORDER:
    qs = groups[c]
    lines.append(f"### ✅{c}（{len(qs)}道）")
    lines.append("")
    for q in qs:
        lines.append(f"#### [{q['title']}]({q['url']})  - {q['difficulty']}")
        lines.append("")
    lines.append("")

with open(f"{BASE}/<主题名>·知识体系清单.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("总题数:", sum(len(v) for v in groups.values()))  # 校验 == len(questions)
```

## 技术原理

- **API 端点**: `POST https://api.mianshiya.com/api/question_bank/list_question`
- **请求体**: `{"current":"1", "pageSize":"200", "questionBankId":"<id>", "tagList":[]}`
- **难度字段**: `difficulty` — `1`=简单, `3`=中等, `5`=困难
- **注意**: 该 API 只返回题目列表（标题+难度+编号），不含答案解析（需登录）。

## 展示结果

向用户报告：题目总数、各分类及题数分布、输出文件路径。提示用户可调整任何一道题的分类归属，调整后重新生成。
