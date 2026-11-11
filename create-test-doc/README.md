# create-test-doc

用于生成和维护标准化后端测试文档的 Skill。

## 文件说明

- `SKILL.md`：Skill 定义、适用场景、工作流程和质量检查清单。
- `backend-test-doc-template.md`：可直接复制使用的后端系统测试文档 Markdown 模板。

## 使用方式

当需要创建后端系统/模块测试文档、测试计划、测试报告或测试用例时，调用此 Skill；结合实际项目材料生成内容，未知信息标记为“待填写”，不得虚构测试执行结果。

## 增量能力

在 Codex 原版基础上增加测试充分性辅助评分，规则见 [references/scoring.md](references/scoring.md)。适用范围、测试类型和验收条件沿用原版；高分不等于验收通过。
