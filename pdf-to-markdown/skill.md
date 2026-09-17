---
name: pdf-to-markdown
description: |
  将 PDF 文件转换为格式规范的 Markdown 文件。保留所有文字内容、图片和代码块。
  当用户提到"PDF转markdown"、"pdf to markdown"、"把PDF转成markdown"、"提取PDF内容为markdown"、
  或者给出 PDF 文件路径并要求转换为文本/笔记时，都应该使用此技能。
  同时适用于网页文章保存为 Markdown 的场景。
---

# PDF 转 Markdown 技能

将 PDF 转换为结构清晰、格式规范的 Markdown 文件，确保图片完整、标题层级正确、
代码块标记准确。

## 工作流程

### 第一步：提取 PDF 内容

**需要同时提取两部分：文本和图片。**

**关键：Windows 环境下 Python 命令选择。** `python3`（Microsoft Store 版）有兼容问题
（exit code 49），必须使用原生安装的 `python`。先用 `which python` 和 `python -c "import fitz; print(fitz.__version__)"` 确认 fitz 可用。

**⚠️ 关键：提取脚本必须在 PDF 文件所在目录运行。** 先用 `cd` 切换到 PDF 所在目录，
确保 `images/` 和 `_extracted_text.txt` 创建在正确位置。**绝对不要在项目根目录运行提取脚本**，
否则 `images/` 会创建在错误位置，导致 Markdown 中图片引用找不到文件。

#### 1a. 提取文本

PyMuPDF（fitz）提取文本质量优于 pdftotext，且可同时获取图片数量。

**不要用 pdftotext。** 它的提取结果对中文 PDF 的排版保留很差。

统一用 PyMuPDF 一次性完成文本提取 + 图片提取，**必须在 PDF 文件所在目录下执行**（**不要写到
`/tmp/`，Windows 原生 Python 不识别这个路径**）：

```python
import fitz, os

doc = fitz.open("PDF文件名.pdf")
# 主题名：Markdown 文件名去掉 ·完整复习笔记 / ·复习笔记 / -完整复习笔记 等后缀
topic = "主题名"
os.makedirs(f"images/{topic}", exist_ok=True)

# 文本保存到当前目录，不要用 /tmp/
with open("_extracted_text.txt", "w", encoding="utf-8") as out:
    for pn in range(len(doc)):
        page = doc[pn]
        text = page.get_text("text")
        images = page.get_images()
        out.write(f"=== PAGE {pn+1} (images: {len(images)}) ===\n")
        out.write(text)
        out.write("\n---END PAGE---\n\n")

        for ii, img in enumerate(images):
            base = doc.extract_image(img[0])
            ext = base["ext"]
            fname = f"prefix_p{pn+1}_{ii}.{ext}"
            with open(os.path.join(f"images/{topic}", fname), "wb") as f:
                f.write(base["image"])
            out.write(f"[IMG SAVED] {fname}\n")

total_pages = len(doc)
doc.close()
print(f"Done! Total pages: {total_pages}")
```

#### 1b. 提取图片

图片已在 1a 的同一脚本中提取完毕，不需要单独执行。

图片命名格式：`前缀_p{页码}_{序号}.{扩展名}`，存放在 `images/<主题名_images>/` 目录下。

**主题名提取规则：** 取 Markdown 输出文件名，去掉 `·完整复习笔记`、`·复习笔记`、`-完整复习笔记` 等学习笔记后缀。
例如 `Redis数据安全性分析·完整复习笔记.md` → 主题名 `Redis数据安全性分析`，图片目录 `images/Redis数据安全性分析/`。

### 第二步：整理内容结构

根据提取的文本，梳理 PDF 的章节结构：

1. 识别一级标题 → 对应 `#` 标题
2. 识别二级标题 → 对应 `## 一、`、`## 二、` 格式（中文数字序号）
3. 识别三级标题 → 对应 `### ✅1.`、`### ✅2.` 格式
4. 识别代码块 → 用对应语言的代码围栏包裹（` ```bash `、` ```sql `、` ```java ` 等）
5. 识别表格 → 用 Markdown 表格呈现

### 第三步：编写 Markdown 文件

**这是最关键的一步。格式不对，整个文件就会渲染错乱。**

#### 格式铁律（五条不可违反的规则）

**规则1：禁止使用 `---` 水平分割线**

Markdown 中 **绝对不要** 出现独立的 `---` 行作为章节分隔符。
章节之间用空行自然分隔即可。`---` 会渲染成 `<hr>` 横线，在笔记中显得多余且不专业。

PDF 原文中的页眉/页脚分隔线也不要保留。

**规则2：每个块级元素之间必须有空行**

```markdown
（空行）
## 一、标题
（空行）
正文内容
（空行）
![图片描述](images/<主题名>/xxx.png)
（空行）
下一段内容
（空行）
```

**规则3：图片引用扩展名必须与实际文件一致**

先 `ls images/<主题名>/` 确认实际扩展名（`.png`、`.jpeg`、`.jpg` 还是 `.gif`），
然后 Markdown 中引用时必须用一致的扩展名。**绝不能假定扩展名。**

**规则4：每页的图片必须全部引用，一张不落**

提取文本时记录了每页的图片数量，写 Markdown 时必须确保：
- 引用图片数量 = 实际提取图片数量
- 图片放在对应页面内容的位置

**规则5：代码块必须指定语言标识**

```markdown
（空行）
```bash
命令内容
```
（空行）
```

常见语言标识：`bash`、`sql`、`java`、`yaml`、`xml`、`python`、`json`、`lua`

#### 文档模板

```markdown
# 主题名称
（空行）
## 📋 知识体系总览
（空行）
```
ASCII树形图
```
（空行）
> 核心概述引用块
（空行）
## 一、第一章名称
（空行）
### ✅1. 小节名称
（空行）
正文内容
（空行）
![图片描述](images/<主题名>/xxx.png)
（空行）
```bash
代码示例
```
（空行）
> **📝 关键点：** 解释说明
（空行）
### ✅2. 小节名称
（空行）
...
（空行）

## 📋 全文总结
（空行）
### ✅1. 总结要点
...
```

### 第四步：验证

转换完成后必须验证：

```bash
# 1. 确认图片引用数 = 实际图片数
grep -c '!\[.*\](images/' 输出文件.md
ls images/<主题名>/ | wc -l

# 2. 确认没有 .jpeg/.png 扩展名不匹配
grep -o 'images/[^)]*' 输出文件.md | while read f; do
  [ -f "$f" ] || echo "缺失: $f"
done

# 3. 确认输出文件中没有 --- 分隔线
grep -n '^---$' 输出文件.md && echo "❌ 发现 --- 分隔线，必须删除！"
```

### 第五步：清理临时文件

```bash
rm -f _extracted_text.txt
```

## Windows 环境注意事项

1. **`python3` 不可用：** Windows Store 版 python3 有兼容问题，必须用 `python` 命令。
   先用 `which python` 确认路径，用 `python -c "import fitz; print(fitz.__version__)"` 确认 PyMuPDF 可用。
2. **不要写 `/tmp/`：** 原生 Windows Python 不识别 `/tmp/` 路径，临时文件写到当前工作目录。
3. **路径格式：** Bash 中写 `"G:/Desktop/..."` 格式（正斜杠），Python 中可用 `os.path.join` 自动适配。
4. **访问 doc 对象必须在 close() 之前：** PyMuPDF 的 `doc.close()` 之后访问 `len(doc)` 或 `doc.page_count` 会抛出 `ValueError: document closed`。如果需要提取总页数等元信息，必须在 `close()` 之前获取并保存到变量中。
5. **⚠️ CWD 必须为 PDF 所在目录：** 提取脚本中 `images/` 和 `_extracted_text.txt` 使用相对路径，
   因此执行 Python 脚本前必须先 `cd` 到 PDF 所在目录。否则图片会创建在错误位置，导致 Markdown 中图片引用全部失效。
   验证时用 `ls images/<主题名>/` 确认图片在输出 `.md` 文件的同级目录下。

## 内容加工原则

1. **不删减原内容**：PDF 中的所有文字、SQL 示例、配置代码必须保留
2. **不保留 `---` 分隔线**：章节之间用空行自然分隔，**绝对不要出现 `---` 水平分割线**
3. **关键概念用引用块标注**：用 `> **📝 核心：**` 或 `> **📝 要点：**` 补充理解
4. **对比信息用表格**：适合快速复习记忆
5. **代码块加语言标识**：`bash`、`sql`、`java`、`yaml` 等
6. **全文用简体中文**：除代码、命令、路径、专有名词外

## 常见错误与排查

### ❌ 图片引用找不到文件

**症状：** 验证时所有图片都报"缺失"，但 `find` 能找到 `.png` 文件。

**根因：** Python 提取脚本在项目根目录运行，`images/` 创建在了根目录，而 Markdown 输出到 PDF 所在子目录。两个目录不一致。

**修复：**
1. 确认 `images/<主题名>/` 在 Markdown 文件同一目录下
2. 如果不在一起，用 `mv` 将 images 目录移到正确位置
3. 如果是子目录结构被展平（文件直接在 `images/` 下），用 `mkdir -p "images/<主题名>" && mv images/prefix_*.png "images/<主题名>/"` 修复

**预防：** 提取前一定先 `cd` 到 PDF 所在目录，确保提取脚本和 Markdown 输出在同一目录下执行。
