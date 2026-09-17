---
name: web-to-markdown
description: 将任意网页文章保存为本地 Markdown 文件，保留原文标题层级、表格、代码块和图片（下载到本地 images/<主题名>/ 目录），并支持将长文逐步精简为复习笔记（要点提取→表格对比→流程图）。当用户提到"保存为markdown""爬取文章""整理成笔记""总结成笔记""网页转markdown""保存网页""提取文章内容"或者给出一个 URL 并希望离线保存/整理时，都应该使用此技能。
---

# Web to Markdown

将网页文章完整提取为本地 Markdown 文件，并在后续可按需逐步精简为结构化复习笔记。

## 前置条件

- Playwright MCP 工具可用（`mcp__playwright__*` 系列工具）
- 目标网页不需要登录或已登录态可用
- 有写入目标目录的权限

## 工作流程

### 阶段一：提取网页内容

#### 1. 导航到目标 URL

```
mcp__playwright__browser_navigate → url: 目标网页地址
```

等待页面加载完成。如果是 JS 动态渲染的页面（如有道云笔记、Notion、飞书文档等），可能需要额外等待：

```
mcp__playwright__browser_wait_for → time: 2-3 秒
```

#### 2. 提取全文文本

使用 `browser_snapshot` 获取页面的无障碍树（accessibility tree），它比直接取 innerText 更能保留结构和语义：

```
mcp__playwright__browser_snapshot
```

返回的文本包含了页面上所有可见元素及其角色（heading、paragraph、list、table 等），根据元素角色还原 Markdown 格式：
- `heading` → `#` / `##` / `###`（按 heading 级别）
- `paragraph` → 正文段落
- `list` + `listitem` → 有序/无序列表
- `table` + `row` + `cell` → Markdown 表格
- `code` → 行内代码或代码块
- `image` → 记录 img 位置和候选 src

#### 3. 提取并下载图片

**先判断页面结构**：查看步骤 2 的 snapshot 结果，如果主要内容在 iframe 中（如：有道云笔记、飞书文档等），则需要分别处理顶层页面和 iframe 内的图片。

**3a. 顶层页面图片提取：**

用 `browser_evaluate` 在页面中运行 JS 获取所有图片 URL：

```javascript
() => {
  const imgs = document.querySelectorAll('img');
  return Array.from(imgs).map((img, i) => ({
    index: i,
    src: img.src,
    alt: img.alt || '',
    width: img.naturalWidth,
    height: img.naturalHeight
  })).filter(x => x.src && !x.src.startsWith('data:') && x.width > 50);
}
```

**3b. iframe 内图片提取（如果有）：**

如果 snapshot 显示内容在 iframe 中，必须单独进入 iframe 提取图片。使用 `browser_evaluate` 访问 `iframe.contentDocument`：

```javascript
() => {
  const iframe = document.querySelector('iframe');
  if (!iframe) return 'no iframe found';
  const imgs = iframe.contentDocument.querySelectorAll('img');
  return Array.from(imgs).map((img, i) => ({
    index: i,
    src: img.src,
    alt: img.alt || ''
  }));
}
```

**3c. 过滤有效图片：**

- 过滤掉 base64 内联图片和小于 50px 的图标类图片
- **过滤掉占位图**：部分平台（如：有道云笔记）会有 `src="http://img/xxx.png"` 这种本地占位图，它们不是真实的可下载资源。只保留完整的 CDN URL（如 `https://note.youdao.com/yws/public/resource/...`）
- 如果 src 是相对路径，拼接页面的 origin 得到完整 URL
- 根据 `alt` 属性给每张图片命名，优先使用 `alt` 中的文件名（如 `QQ_1725009412511.png`）作为文件命名参考

注意事项：
- **必须带 referer** 下载，否则部分站点会拒绝访问

下载命令（Windows bash 环境可能没有 `wget`/`curl`，但 `curl` 通常可用）：

```bash
curl -sL -H "Referer: <页面URL>" -o "<目标路径>" "<图片URL>"
```

**大批量图片分批下载：** 图片超过 10 张时，分成 2-3 批并行下载（每批 5-6 张），避免单次命令过长超时。每批内部用 `&&` 串行执行，批次之间用并行的 Bash 调用。

图片存放在 `images/<主题名>/` 子目录中，主题名取输出 Markdown 文件名去掉 `·完整复习笔记`、`·复习笔记`、`-完整复习笔记` 等学习笔记后缀，以及去掉 `2. `、`一、` 等序号前缀。

```
示例：Redis数据安全性分析·完整复习笔记.md → images/Redis数据安全性分析/
示例：2. Future&CompletableFuture实战.md → images/Future和CompletableFuture实战/
```

> ⚠️ **关键：图片子目录命名规范**
> 1. **不能包含空格** — 空格在 Markdown 路径中兼容性差，部分渲染器无法识别
> 2. **不能包含 `&`、`%`、`#`、`?` 等特殊字符** — `&` 会被误解析为 HTML 实体
> 3. **只使用中文、字母、数字、下划线 `_`、连字符 `-`** — 如需替换 `&` 用 `和` 或 `-`
> 4. **去掉序号前缀** — `2. Future实战` → `Future实战`，避免句点被误解析

文件命名规则：`{序号}_{描述性名称}.png`（同样不包含空格和特殊字符）。

#### 4. 生成 Markdown 文件

根据步骤 2 提取的结构和步骤 3 的本地图片路径，组装完整的 Markdown 文件。

**格式铁律（必须遵守）：**

1. **块级元素之间必须有空行**：`##` 标题、图片、代码块、表格前后各留一个空行，否则渲染会错乱
2. **不保留 `---` 分隔线**：章节之间用空行自然分隔，不使用水平分割线
3. **代码块必须指定语言标识**：`bash`、`sql`、`yaml`、`xml`、`python`、`java` 等
4. **图片引用路径统一**：使用相对路径 `images/<主题名>/xxx.png`
5. **文件名格式**：`{原文标题或序号}.md`
6. **图片路径禁止 URL 编码**：路径中直接使用原始中文文件名（如 `结构图.png`），**严禁**使用 `%E5%AE%9E` 之类的百分号编码 — 本地 Markdown 渲染器按文件系统路径查找，不会解码 URL 编码

**文档模板：**

```markdown
# 主题名称
（空行）
## 一、章节名称
（空行）
正文内容
（空行）
![图片描述](images/<主题名>/xxx.png)
（空行）
```bash
代码内容
```
