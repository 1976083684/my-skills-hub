---
name: create-test-doc
description: Create standardized backend system testing documentation and test-case templates in Markdown. Use when the user asks to create, draft, standardize, or update backend test documents, test plans, test reports, or backend test-case specifications.
---

# create-test-doc

## Purpose

Create clear, reusable backend testing documentation in Markdown. The document should explain what is tested, how it is tested, the expected results, the actual results, defects, residual risks, and the testing conclusion.

Use this skill for Java backend projects and other backend systems. Adapt to the actual technology stack and project conventions; do not assume Spring Boot, MyBatis, a particular database, or a message broker unless the user or project materials confirm them.

## Core rules

1. **Conclusion first.** Briefly state the document type and scope before presenting the artifact.
2. **Use Chinese by default**, unless the user asks for another language.
3. **Do not invent project facts.** Use `待填写` for unknown project-specific values and explicitly identify assumptions.
4. **Fit the scope.** Support module testing, system testing, developer self-testing, API testing, regression testing, and acceptance testing. Do not force every test category into every project.
5. **Separate document and cases.** The test document defines scope, strategy, environment, execution, defect tracking, and conclusions. Detailed test cases describe steps and expected results. They may be embedded or separated depending on the user's needs.
6. **Cover backend risks.** Where applicable, consider business rules and state transitions, request validation, response codes and schemas, database consistency, transaction boundaries, idempotency, permissions, concurrency, external dependencies, MQ retry/replay, scheduled jobs, and regression.
7. **Keep evidence traceable.** Include case IDs, API IDs, defect IDs, execution status, test date/owner, and evidence references where useful.
8. **Do not claim tests were executed** unless execution evidence is supplied or tools were actually used to run them. Distinguish planned tests from completed tests.
9. **Respect project boundaries.** If project files are provided, inspect relevant files before documenting project-specific behavior. Do not change source code when the task is only to create documentation.
10. **Avoid unsafe or destructive test actions.** Call out test-environment requirements and data-reset risks. Do not execute destructive actions without explicit authorization.

## Workflow

1. Identify the requested artifact:
   - Test plan / test strategy
   - Module test document
   - System test document
   - Test report
   - Detailed test-case set
   - API test document
2. Determine scope and available evidence:
   - Project/system/module name and release version
   - Requirements, design documents, API definitions, database schema, and relevant source code
   - Test environment, dependencies, and acceptance criteria
3. If the user supplied project files or references prior project documents, read the relevant material before writing project-specific test cases. If essential information is missing, proceed with a reusable template and mark unknowns as `待填写`; ask a question only when the task cannot reasonably proceed.
4. Create a Markdown artifact with appropriate sections from the template below. Remove irrelevant sections instead of filling the document with empty boilerplate.
5. Ensure each detailed test case has an observable expected result. Add database checks or logs where the result cannot be verified from the API response alone.
6. Include a summary of what is covered, what remains untested, unresolved risks, and the conditions for passing.
7. If execution results are not provided, set execution statuses to `未执行` and leave actual results blank or `待执行`.
8. If the user requests a downloadable skill package, include this `SKILL.md` and a reusable template file in a ZIP archive.

## Recommended document structure

For a standard backend system test document, use these sections as applicable:

1. Document information
2. Test overview and objectives
3. Scope, exclusions, prerequisites, and limitations
4. Test strategy and test types
5. Test environment and test data
6. Test case list and detailed cases
7. API test records
8. Database and business-data verification
9. Non-functional testing
10. Defect tracking and regression testing
11. Execution statistics
12. Test conclusion, residual risks, and recommendations
13. Appendix: request/response samples, SQL, logs, screenshots, automation reports, and revision history

## Test-case design checklist

For each relevant business function, consider:

- Happy path and business-state transitions
- Missing, malformed, invalid, duplicate, and out-of-range parameters
- Empty results, nonexistent records, duplicate records, and boundary values
- Create/update/delete/query behavior and database consistency
- Transaction commit/rollback and partial-failure behavior
- Authentication, operation authorization, and data-scope authorization
- Duplicate requests and idempotency
- Concurrent updates and race conditions
- External service timeout, failure, and malformed response
- MQ duplicate delivery, retry, consumption failure, ordering, and replay when applicable
- Scheduled-job timing, repeated execution, recovery, and overlapping runs when applicable
- Pagination, sorting, filtering, and large result sets
- Regression coverage for dependent functions

Prioritize tests by business criticality and risk. Do not require every item for every endpoint.

## Status and severity conventions

Suggested case execution statuses:
- `未执行`
- `通过`
- `失败`
- `阻塞`
- `不适用`

Suggested priorities:
- `P0`: release-blocking or critical business risk
- `P1`: important core flow
- `P2`: normal functional coverage
- `P3`: low-risk or supplementary coverage

Suggested defect severities:
- `致命`
- `严重`
- `一般`
- `轻微`

Adapt these labels to the team's existing conventions if they differ.

## Pass-rate and conclusion rules

- State the denominator used for pass rate, for example `通过用例数 ÷ 已执行用例数`.
- Do not count blocked or unexecuted cases as passed.
- Do not use pass rate alone as the release decision.
- Base the conclusion on agreed acceptance criteria, critical-case results, open defects, and residual risks.
- Use `通过`, `有条件通过`, or `不通过` only when supported by the available evidence.

## Quality checklist before delivery

- [ ] Scope and exclusions are explicit.
- [ ] Environment and test-data assumptions are identified.
- [ ] Important normal, negative, boundary, and integration scenarios are covered.
- [ ] Each detailed case has steps and observable expected results.
- [ ] API and database checks are included where applicable.
- [ ] Actual results are not fabricated.
- [ ] Defects and regression results are traceable.
- [ ] Execution statistics use a clear calculation rule.
- [ ] Untested areas and residual risks are disclosed.
- [ ] Irrelevant sections are removed or marked as not applicable.

## Output format

- Prefer Markdown (`.md`) with readable headings and tables.
- Use a consistent ID scheme such as `TC-001`, `API-001`, `DB-001`, `BUG-001`, and `RISK-001`.
- For a reusable blank template, use `待填写` and default case status `未执行`.
- For a project-specific document, derive details from supplied requirements, API docs, schemas, or source files and cite/refer to the evidence where possible.

## 辅助评分机制

在上述原版工作流和文档结构基础上，仅增加测试充分性评分；不改变文档适用范围、用例设计、执行状态和验收规则。

- 生成测试报告或评审已有执行结果时，读取 [评分规则](references/scoring.md)，在测试结论中附评分及问题明细。
- 测试计划、用例设计和空白模板只保留评分栏位，标记 `未评分（尚未执行）`。
- 根据需求、接口、业务规则和验收条件确定范围；Git Diff 只是辅助依据，不能排除用户指定的存量功能测试。
- 评分只描述约定范围内、现有证据支持的测试充分性，不代表代码质量、代码覆盖率或发布批准；验收结论仍按上文 Pass-rate and conclusion rules 确定。
- 主模板为 [后端测试文档模板](backend-test-doc-template.md)，按所需文档类型裁剪；评分记录见评分规则中的模板。