---
name: youdao-to-markdown
description: >
  将有道云笔记分享链接直接转换为 Markdown 文件，无需浏览器自动化。
  当用户提供有道云笔记分享链接（share.note.youdao.com / note.youdao.com/s/）
  并要求"下载笔记"、"转为markdown"、"保存为本地文件"、"提取内容"时使用此技能。
  也适用于批量下载有道云笔记分享链接的场景。
  即使用户只说"把这个有道云笔记保存下来"也应该触发此技能。
---

# 有道云笔记分享链接 → Markdown 转换

## 工作流程

### 第一步：从 URL 提取 shareKey

有道云笔记分享链接有两种格式：
- `https://share.note.youdao.com/ynoteshare/index.html?id={shareKey}&type=note`
- `https://note.youdao.com/s/{shareKey}`（短链接，需跟随重定向获取真实 shareKey）

从 URL 参数 `id` 中提取 `shareKey`（通常是 32 位十六进制字符串）。

### 第二步：调用 API 获取笔记内容

核心 API：

```
GET https://note.youdao.com/yws/api/note/{shareKey}
  ?sev=j1
  &editorType=1
  &unloginId={随机UUID}
  &editorVersion=new-json-editor
  &sec=v1
```

关键请求头：
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Referer: https://share.note.youdao.com/ynoteshare/index.html?id={shareKey}&type=note
```

**关键注意事项：**

1. `editorVersion=new-json-editor` **必须传**。不传此参数会返回老版本 XML 格式的"版本过低"占位内容，而非真实笔记。
2. `unloginId` 是随机 UUID，用于未登录用户的匿名标识，任意生成即可。
3. 不需要 Cookie 或登录态，API 完全公开。
4. 也提供元数据 API（可选，用于获取分享者信息等）：
   ```
   GET https://note.youdao.com/yws/api/personal/share?method=get&shareKey={shareKey}
   ```

### 第三步：解析 JSON block 树

API 返回格式：
```json
{
  "tl": "笔记标题",
  "content": "{...JSON字符串...}"
}
```

`content` 字段是 JSON 字符串，解析后的 block 树结构：

```
根节点
├── "5": [block数组]  // 内容块列表
│   ├── "6": block类型
│   │   ├── "h"  → 标题      (层级在 "4.l": "h1"/"h2"/"h3"...)
│   │   ├── "?"  → 段落/未知
│   │   ├── "q"  → 引用块
│   │   ├── "l"  → 列表      (类型在 "4.lt": "unordered"/"ordered", 层级 "4.ll": 1/2/3)
│   │   ├── "cd" → 代码块    (语言在 "4.la", 代码行 "6":"cl")
│   │   ├── "im" → 图片      (URL在 "4.u")
│   │   └── "t"  → 表格      (列宽 "4.cw", 行高 "4.rh")
│   ├── "5": [子block数组]    // 递归子内容
│   └── "7"/"8": 文本内容    // "7"是runs数组, "8"是具体文字
└── "title": 标题
```

文本行内样式在 `"9"` 数组中：
- `"2":"b"` → 粗体
- `"2":"i"` → 斜体
- `"2":"u"` → 下划线
- `"2":"c"` → 文字颜色（可忽略）
- `"2":"fs"` → 字号（可忽略）
- `"2":"bg"` → 背景色（可忽略）

链接块：`"2":"3"` 类型，URL 在 `"4.hf"`。

### 第四步：转换为 Markdown

转换映射：

| 有道类型 | Markdown |
|----------|----------|
| `h` (l=h1) | `# text` |
| `h` (l=h2) | `## text` |
| `h` (l=h3) | `### text` |
| `?` (段落) | 直接输出文字 |
| `q` (引用) | `> text` |
| `l` (无序) | `- text` (按 `ll` 缩进) |
| `l` (有序) | `1. text` (按 `ll` 缩进) |
| `cd` (代码) | ` ```lang\ncode\n``` ` |
| `im` (图片) | `![image](url)` |
| `t` (表格) | Markdown 表格 |

**⚠️ 文本提取必须递归** — 表格单元格的结构是 `tc → para → text_block → runs`，共三层嵌套。简单的单层遍历会返回空文本。始终递归进入没有 `"7"` 但有 `"5"` 的子节点。

### 第五步：后处理

运行转换后执行以下清理：

1. **跳过重复标题**：如果第一个 h1 block 的文本与 meta `tl` 标题相同（需先做 Unicode 规范化，`\xa0` → ` `），则跳过。
2. **清理空标题**：跳过 `extract_text()` 返回空串的 `h` 类型 block。
3. **清理空列表项**：用正则 `\n+( {0,6})[-*+]\s*\n+` 多次迭代清理文本为空的 `l` 类型 block。
4. **压缩多余空行**：4个及以上连续空行 → 3个空行。
5. **过滤空 block**：跳过类型为 `?` 且无文本内容的 block。

## 常见陷阱（务必避免）

### 1. API 参数缺失导致占位内容
**错误**：`/yws/api/note/{shareKey}` 无参数 → 返回老 XML 格式的"版本过低"提示。
**正确**：必须带 `editorVersion=new-json-editor&unloginId={UUID}&sev=j1&editorType=1`。

### 2. 表格内容为空
**错误**：`extract_text` 只遍历 `block["5"][*]["7"]`，表格 cell 的 `"7"` 在更深层。
**正确**：文本提取必须递归 — 当 child 没有 `"7"` 但有 `"5"` 时，递归进入。
```python
def extract_text(block):
    texts = []
    for child in block.get("5", []):
        has_runs = False
        for run in child.get("7", []):
            if run.get("8"):
                texts.append(run["8"])
                has_runs = True
        if not has_runs and child.get("5"):
            texts.append(extract_text(child))  # 递归
    return "".join(texts)
```

### 3. 标题重复
**错误**：meta 的 `tl` 标题和内容第一个 h1 都输出了。
**正确**：比较时先做 Unicode 规范化（`\xa0` → ` `），匹配则跳过第一个 h1。

### 4. Unicode 不换行空格 `\xa0`
有道云笔记内容中 `\xa0` (non-breaking space) 频繁出现，在标题比较、文本规范化时都要替换为普通空格。

### 5. 末尾残留空列表项
**错误**：源 JSON 中存在文本为空的列表 block，正则不够强。
**正确**：用 `\n+( {0,6})[-*+]\s*\n+` 3 次迭代清理，最后加兜底正则 `\n( {0,6})[-*+] ?\n`。

### 6. Windows 编码问题
**错误**：`UnicodeEncodeError: 'gbk' codec can't encode character`。
**正确**：Python 脚本始终用 `-X utf8` 参数运行，或设置 `PYTHONIOENCODING=utf-8`。

### 7. Windows 无 `/tmp/` 路径
**错误**：`FileNotFoundError: /tmp/youdao_note_raw.json`。
**正确**：使用 `$TEMP` 或 `os.environ.get('TEMP')` 获取临时目录。

### 8. Bash 特殊字符转义
**错误**：反引号 ```、感叹号 `!` 在 bash 命令中触发语法错误。
**正确**：Python 代码用 heredoc `<<'PYEOF'` 传入，或写入 `.py` 文件后执行。

## 使用内置转换脚本

技能附带了经过实战验证的转换脚本，推荐直接使用：

```bash
# 1. 先下载 JSON
curl -s "https://note.youdao.com/yws/api/note/{shareKey}?sev=j1&editorType=1&unloginId=$(uuidgen)&editorVersion=new-json-editor&sec=v1" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Referer: https://share.note.youdao.com/ynoteshare/index.html?id={shareKey}&type=note" \
  -o "$TEMP/youdao_note.json"

# 2. 运行转换
python -X utf8 scripts/convert_youdao.py "$TEMP/youdao_note.json" -o output.md
```

## 输出格式

生成的 Markdown 文件遵循以下结构：
```markdown
# 笔记标题

> **来源：** 有道云笔记分享

## 一、第一个章节
...
## 二、第二个章节
...
```

- 图片 URL 保留有道云 CDN 在线地址（可后续本地化）
- 代码块保留原始缩进和格式
- 表格使用标准 Markdown 表格语法
