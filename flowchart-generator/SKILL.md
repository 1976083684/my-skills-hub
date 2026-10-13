---
name: flowchart-generator
description: 根据用户提供的流程生成 Markdown 流程图；默认仅输出兼容 Mermaid，明确要求 draw.io 时才生成原生编辑源，明确指定 SVG 时区分普通展示 SVG 与包含 draw.io 编辑模型的 SVG；本地 draw.io 为可选工具。
---

# 流程图生成

仅负责用户提供流程的绘图、格式选择和保存。不定义系统分析方法、不引用系统分析模板、不主动扫描仓库或补充业务。

## 默认格式与两种交付方式

默认只在 Markdown 中展示纯 Mermaid，不生成 `.drawio`、SVG 或交付图片目录。未指定、表达不清或无法判断时，也直接采用纯 Mermaid，不询问格式；“正式展示”“精致”等描述不自动触发额外文件。用户明确要求 draw.io 时才生成原生编辑源；明确指定 SVG 时按下方规则选择普通展示 SVG 或原生 draw.io＋嵌入模型的 SVG。每次仅交付一份 Markdown。

1. **默认方式，日常快速生成、主要通过源码维护：纯 Mermaid。** Markdown 内直接保存 Mermaid 源码，采用旧版兼容语法与清新配色；是否启用 ELK 取决于目标渲染器能力。旧版不支持 ELK 时明确采用 Dagre 兼容回退，不把回退称为 ELK。用户明确要求额外生成 draw.io 时，才为指定范围的图另存可编辑的 mxGraph 模型；Markdown 仍保留 Mermaid，不自动添加编辑源链接，不导出 SVG。
2. **明确指定 SVG 时，按编辑需求选择。** 仅要求 SVG、用于展示或由 Mermaid 转为图片时，可用 Mermaid 渲染器生成普通 SVG，不额外生成 `.drawio`。明确要求 draw.io、原生节点编辑或包含 draw.io 编辑模型的 SVG 时，先生成原生 mxGraph 模型 `.drawio`，再通过 draw.io 桌面端或网页版导出包含编辑模型的 SVG。普通 SVG 是有效的矢量图，但不能当作包含 draw.io 原生编辑模型的 SVG 交付。

## 保存规则

遵循用户指定的 Markdown 路径，不写死业务目录。

- 默认 Mermaid：只交付 Markdown，不生成 draw.io、SVG 或交付图片目录。校验中间文件放临时目录。
- 明确指定 draw.io：只为用户指定的图或范围生成原生编辑源，保存在 Markdown 同级 `./images/{md文件名不含扩展名}/`；Markdown 继续展示 Mermaid，默认不添加编辑源链接，不导出 SVG。
- 明确指定 SVG：图片保存在上述目录，Markdown 用相对路径嵌入 SVG；仅在要求 draw.io 原生可编辑交付时，同时保存并链接对应 `.drawio`。
- 明确生成文件时按图标题使用可辨识名称，如 `订单转换-正式定论.drawio`；对应 SVG 使用相同文件名主体。重名时追加序号，避免仅靠 `diagram-001` 等连续编号识别图。
- 只有用户要求更新时覆盖已有文件，不删除无关文件，也不额外交付另一套 Markdown。

## 流程与样式

保持用户提供的节点、条件、连线方向和虚实关系。调整布局不能增加业务关系；需要拆图时保留跨图对应关系。

统一清新配色：业务处理蓝色 `#EFF6FF/#60A5FA`；单证与结果绿色 `#ECFDF5/#34D399`；资格判断橙色 `#FFF7ED/#FB923C`；支撑和来源灰色 `#F8FAFC/#94A3B8`。文字 `#1E293B`，实线 `#64748B`，依赖虚线 `#94A3B8`。节点用圆角矩形，条件用菱形；避免阴影和过粗连线。

Mermaid：节点文本全部双引号；子图英文 ID 加引号标题；标签用带引号的管道形式；换行用引号内 `<br/>`。详细版本选择、两套提示词和 draw.io 导出步骤见 [references/提示词与使用说明.md](references/提示词与使用说明.md)。

## 检查与工具边界

Mermaid 在目标版本验证语法和样式，校验文件使用临时目录。现代 CLI 渲染通过不代表 Mermaid 8.8.3 可用；未在目标环境验证时明确说明。初始化配置、ELK 未应用时不能声称布局生效。

draw.io 编辑源使用独立节点及引用真实节点的连线，不以整图图片代替模型；生成 XML 不依赖本地 draw.io。检查节点文字、条件和连线关系与 Mermaid 或用户流程一致。渲染后检查文字可读、无裁切、连线绕行和分支清晰；未渲染时不得声称视觉检查通过。

### 工具选择与失败回退

- 本地 draw.io 是可选导出工具，不是技能运行前提。默认 Mermaid 不探测 draw.io；仅生成 `.drawio` 时直接构造模型，不为此寻找桌面端。
- 需要 draw.io 导出时，优先使用已知可用的桌面端；未知时仅检查 PATH、用户指定位置及少量常见安装目录一次。未找到立即停止查找，不递归搜盘、反复扩大范围或自行安装。
- 桌面端不可用时，可通过现有浏览器控制工具使用 draw.io 网页版导出，启用 Include a copy of my diagram。网页版是否可用以当前网络、工具能力及文件读写能力为准；涉及外部传输时遵循用户和环境的数据访问限制，不绕过限制。
- 包含 draw.io 编辑模型的 SVG 须由 draw.io 实际导出；解析恢复模型并比较原生对象、节点文字与连线端点，条件允许时重新打开 SVG 验证可单独编辑。不能仅凭文件后缀、元数据标记或嵌入任意 XML 判断验证通过。
- 桌面端与网页版均无法导出时，保存 `.drawio` 并明确说明 SVG 尚未完成、缺少何种能力；不得伪造已完成或自动用普通 SVG 替代用户明确要求的原生可编辑 SVG。
- 普通展示 SVG 可使用 Mermaid 渲染器生成。现有 `scripts/render_diagrams.py --mode svg` 可用于 Mermaid 普通 SVG 的生成或临时验证，使用前检查脚本参数与产物；不宣称具备 draw.io 原生编辑能力。`--mode mermaid` 仅保留源码，不自动改配色或兼容语法；`mermaid-config.json` 不控制 Typora 或原生 draw.io。

### Mermaid 8.8.3 颜色兼容补充

目标为 Mermaid 8.8.3 时，流程图样式优先采用 CSS 英文命名色（aliceblue、cornflowerblue、honeydew、mediumseagreen、oldlace、darkorange、whitesmoke、lightslategray、darkslategray、slategray），避免旧宿主对边样式中的十六进制颜色产生实体转义异常。仍使用处理蓝、结果绿、判断橙、支撑灰。不要以现代渲染器验证代替目标版本验证；交付前用 8.8.3 实际渲染所有图。
