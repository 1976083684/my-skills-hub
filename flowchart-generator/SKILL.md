---
name: flowchart-generator
description: 根据用户提供的流程生成 Markdown 流程图；默认仅输出兼容 Mermaid，明确要求 draw.io 时才生成原生编辑源，明确指定 SVG 时交付嵌入编辑模型的 SVG。
---

# 流程图生成

仅负责用户提供流程的绘图、格式选择和保存。不定义系统分析方法、不引用系统分析模板、不主动扫描仓库或补充业务。

## 默认格式与两种交付方式

默认只在 Markdown 中展示纯 Mermaid，不生成 `.drawio`、SVG 或交付图片目录。未指定、表达不清或无法判断时，也直接采用纯 Mermaid，不询问格式；“正式展示”“精致”等描述不自动触发额外文件。用户明确要求 draw.io 时才生成原生编辑源；明确指定 SVG 时才使用原生 draw.io＋嵌入模型的 SVG。每次仅交付一份 Markdown。

1. **默认方式，日常快速生成、主要通过源码维护：纯 Mermaid。** Markdown 内直接保存 Mermaid 源码，采用旧版兼容语法与清新配色；是否启用 ELK 取决于目标渲染器能力。旧版不支持 ELK 时明确采用 Dagre 兼容回退，不把回退称为 ELK。用户明确要求额外生成 draw.io 时，才为指定范围的图另存可编辑的 mxGraph 模型；Markdown 仍保留 Mermaid，不自动添加编辑源链接，不导出 SVG。
2. **明确指定 SVG 时，正式展示、布局精致、需要手动编辑：原生 draw.io＋嵌入模型的 SVG。** 先生成可编辑的 mxGraph 模型 `.drawio`，再通过 draw.io 导出带编辑模型的 SVG，最后在 Markdown 中引用。不能用 Mermaid 导出的普通 SVG 代替这一方式。

## 保存规则

遵循用户指定的 Markdown 路径，不写死业务目录。

- 默认 Mermaid：只交付 Markdown，不生成 draw.io、SVG 或交付图片目录。校验中间文件放临时目录。
- 明确指定 draw.io：只为用户指定的图或范围生成原生编辑源，保存在 Markdown 同级 `./images/{md文件名不含扩展名}/`；Markdown 继续展示 Mermaid，默认不添加编辑源链接，不导出 SVG。
- 明确指定 SVG：图片和编辑源统一保存在上述目录；Markdown 用相对路径嵌入 SVG，并提供对应 `.drawio` 的相对链接。
- 明确生成文件时按图标题使用可辨识名称，如 `订单转换-正式定论.drawio`；对应 SVG 使用相同文件名主体。重名时追加序号，避免仅靠 `diagram-001` 等连续编号识别图。
- 只有用户要求更新时覆盖已有文件，不删除无关文件，也不额外交付另一套 Markdown。

## 流程与样式

保持用户提供的节点、条件、连线方向和虚实关系。调整布局不能增加业务关系；需要拆图时保留跨图对应关系。

统一清新配色：业务处理蓝色 `#EFF6FF/#60A5FA`；单证与结果绿色 `#ECFDF5/#34D399`；资格判断橙色 `#FFF7ED/#FB923C`；支撑和来源灰色 `#F8FAFC/#94A3B8`。文字 `#1E293B`，实线 `#64748B`，依赖虚线 `#94A3B8`。节点用圆角矩形，条件用菱形；避免阴影和过粗连线。

Mermaid：节点文本全部双引号；子图英文 ID 加引号标题；标签用带引号的管道形式；换行用引号内 `<br/>`。详细版本选择、两套提示词和 draw.io 导出步骤见 [references/提示词与使用说明.md](references/提示词与使用说明.md)。

## 检查与工具边界

Mermaid 在目标版本验证语法和样式，校验文件使用临时目录。现代 CLI 渲染通过不代表 Mermaid 8.8.3 可用；未在目标环境验证时明确说明。初始化配置、ELK 未应用时不能声称布局生效。

draw.io 编辑源使用独立节点及引用真实节点的连线，不以整图图片代替模型；检查节点文字、条件和连线关系与 Mermaid 或用户流程一致，文字可读、无裁切、连线绕行和分支清晰。仅在明确指定 SVG 时执行导出：SVG 必须由 draw.io 导出并包含可恢复的编辑模型；检查原生对象数量、节点文字和连线端点与源模型一致，并验证模型可恢复，条件允许时在 draw.io 重新打开 SVG 验证。未检查的项目如实说明。

现有 `scripts/render_diagrams.py` 是 Mermaid 辅助工具：`--mode mermaid` 仅保留源码，不自动改配色或兼容语法；`--mode svg` 是历史 Mermaid 渲染能力，仅用于临时验证，不属于正式 draw.io 交付链路。`mermaid-config.json` 也仅作用于该工具，不控制 Typora 或原生 draw.io。不要将它们误用为正式 SVG 生成器。

### Mermaid 8.8.3 颜色兼容补充

目标为 Mermaid 8.8.3 时，流程图样式优先采用 CSS 英文命名色（aliceblue、cornflowerblue、honeydew、mediumseagreen、oldlace、darkorange、whitesmoke、lightslategray、darkslategray、slategray），避免旧宿主对边样式中的十六进制颜色产生实体转义异常。仍使用处理蓝、结果绿、判断橙、支撑灰。不要以现代渲染器验证代替目标版本验证；交付前用 8.8.3 实际渲染所有图。
