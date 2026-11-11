# create-module-migration-doc

为指定系统的业务模块生成代码迁移前的「迁移清单」Markdown 文档。

## 目录结构

```text
create-module-migration-doc/
├── SKILL.md
└── templates/
    └── module-migration-doc-template.md
```

## 使用方式

将 `create-module-migration-doc/` 目录放入所使用的 Agent Skills 技能目录中（如 `~/.claude/skills/`）。调用技能时，提供系统名称、模块名称、项目源码路径或迁移范围说明，技能会按模板生成迁移清单文档。

## 输出

- 文档命名：`{系统名}{模块名}迁移清单.md`（示例：`订单系统支付模块迁移清单.md`）。
- 文档包含：文档信息、迁移范围、待迁移文件清单、关联依赖及迁移说明、迁移验证、迁移确认。

本技能仅负责迁移前盘点，不执行代码迁移。
