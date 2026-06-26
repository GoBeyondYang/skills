---
name: business-conflict-analyzer
description: >
  Analyzes business impact of API contract/field/schema changes in Java, Spring, Django, DRF, FastAPI, Flask, TypeScript, NestJS, Go, and Kotlin projects.
  Detects breaking changes in DTOs, VOs, interfaces, ORM models, serializers, database DDL, Feign/RPC clients, message/event schemas, config properties, enums, API endpoints, response formats, validation/cache/transaction annotations, async/scheduled tasks, and component props.
  Also detects data migration needs and approval workflows.
  — Trigger phrases —


  Chinese: "影响分析", "冲突分析", "兼容",
  "字段变更", "删字段", "新增字段", "增加字段", "加一个", "字段类型", "类型变了",
  "列改名", "表结构", "数据库变更", "DDL变更", "删列", "新表", "增表", "建表", "审批",
  "数据迁移", "存量数据",
  "API升级", "API版本", "新版本", "新接口", "接口变更", "接口路径", "路径变了",
  "返回值", "响应格式", "参数变了", "对外接口", "端点", "路由",
  "RequestMapping", "GetMapping", "PostMapping",
  "配置项", "配置新增", "配置删除",
  "消息队列", "消息体", "消息格式", "MQ", "消费者",
  "枚举", "新增枚举", "废弃枚举", "废弃值", "已废弃", "废弃的枚举", "新状态", "加新的",
  "注解", "@NotNull", "@Cacheable", "校验", "校验规则", "校验收紧",
  "缓存", "缓存key", "事务", "事务注解", "去掉事务", "传播级别",
  "定时任务", "频率",
  "Feign", "RPC", "fallback", "降级",
  "会不会影响", "会影响哪些", "要通知谁", "风险是什么", "影响范围",
  "需要升级", "要不要发版", "前端要改", "测试要改",


  English: "breaking change", "impact analysis", "compatibility", "backward compatibility",
  "what breaks", "will this break", "does this break",
  "what's affected", "what services", "who to notify",
  "data migration", "rename field", "field removed", "drop column",
  "schema change", "interface change", "response format", "response changed", "format changed",
  "message format", "consumer", "needs update", "need to update",
  "API contract", "endpoint", "new version", "version upgrade",
  "deprecated", "approval".
---

# Business Conflict Analyzer / 业务冲突分析 Skill

## Overview / 概述

This Skill is an **inherent instinct** of the AI coding assistant. While generating or modifying code, the AI spontaneously detects changes that affect external contracts (API upgrades, field changes, protocol changes), automatically triggers the analysis pipeline, and outputs a plain-business-language *Impact Analysis Report* for human decision-making.

本 Skill 是 AI 的"内置本能"。AI 在执行代码生成或修改任务时，自发感知到涉及外部依赖变更（API 升级、字段变更、协议变化），自动触发分析流程，输出纯业务语言的《影响分析报告》并推送人类决策。

**Core idea / 核心理念**: No human needs to manually navigate to any system to "start analysis" — the AI notices the change while writing code, analyzes it, pushes the report, and waits for a decision.

---

## Trigger Conditions / 触发条件

The AI should **auto-trigger** this Skill when performing any of the following operations:
AI 在执行以下任一操作时，应**自动触发**本 Skill：

### Auto-Trigger / 自动触发（无需人类指令）

| Scenario / 场景 | Identification / 识别特征 |
|----------------|-------------------------|
| API request/response field change | DTO/VO class add/delete/modify fields, `@RequestBody`/`@ResponseBody` changes |
| Interface method signature change | Interface method parameters, return type, or exception declarations change |
| RPC/Feign interface change | `@FeignClient` definition changes, or downstream service contract changes |
| Database DDL change | `ALTER TABLE`, `DROP COLUMN`, `CREATE TABLE`, etc. |
| Message/event schema change | MQ message body field add/delete/modify |
| Config property change | `application.yml`, config center item add/delete/rename |

### On-Demand / 按需触发（建议分析）

| Scenario / 场景 | Description / 说明 |
|----------------|-------------------|
| Enum value changes | Add/deprecate enum constants |
| Core business logic refactor | Payment, refund, inventory logic changes |
| Annotation/validation rule changes | `@NotNull` → `@Nullable`, `@Validated` scope changes |

---

## Analysis Pipeline / 分析流程

### Step 1: Extract Diff / 提取差异

- Run `scripts/diff_analyzer.py`
- Input: `git diff` (or IDE changes)
- Output: Structured change manifest with file paths, change types (ADD/MODIFY/DELETE), symbols (field/method names), and granularity

### Step 2: Map Impact / 映射影响

- Run `scripts/impact_mapper.py`
- Input: Step 1 structured manifest
- Core logic: Traverse each change, search project references, consult `references/common_patterns.md`
- Output: Impact matrix (consumer impacts, data compatibility, frontend/test impacts)

### Step 3: Generate Report / 生成报告

- Run `scripts/report_generator.py`
- Input: Step 2 impact matrix
- Core logic: Translate technical language → business language
- Output: Plain-business-language *Business Impact Analysis Report*

### Step 4: Push for Decision / 推送决策

- Report pushed directly to human (code review comment / IM / inline display)
- Wait for human feedback:
  - **Accept / 采纳** → AI proceeds with changes
  - **Reject / 拒绝** → AI rolls back, records reason
  - **Revision / 修改建议** → AI adjusts approach based on feedback and re-analyzes

---

## Output Specification / 输出规范

### Report Structure / 报告结构

```markdown
## ⚠️ Business Impact Analysis Report / 业务影响分析报告

### Change Summary / 变更摘要
[One sentence: what changed]

### Change Details / 变更明细
[Per-file: tech change → business language translation]

### Impact Scope / 影响范围
[Affected features / services / data compatibility]

### Risk Assessment & Recommendation / 风险等级与建议
Risk level: High / Medium / Low

### Decision / 决策
- [ ] Accept / 采纳
- [ ] Reject / 拒绝
- [ ] Revision / 修改建议
```

### Risk Levels / 风险等级

| Level / 等级 | Meaning / 含义 | Action / 处理方式 |
|-------------|---------------|-----------------|
| **High** 🔴 **高** | Downstream compile failure / runtime exception / data loss | Must be confirmed by business owner, version upgrade required |
| **Medium** 🟡 **中** | Behavior change with backward compatibility | Notify stakeholders, include in iteration plan |
| **Low** 🟢 **低** | New capability / internal refactor | Auto-handle, documentation notice suffices |

### Translation Rules / 翻译规则

| Technical / 技术语言 | → | Business / 业务语言 |
|---------------------|:-:|--------------------|
| "Delete UserDTO.mobile field" | → | "User API will no longer return the mobile phone number field" |
| "ALTER TABLE user DROP COLUMN mobile" | → | "User table will drop the mobile column; existing data must be migrated" |
| "Signature getUser(Long) → getUser(String)" | → | "User lookup method changed — input from numeric ID to string UID" |
| "Enum new constant REFUNDING" | → | "Order lifecycle gains a new 'Refunding' state" |

---

## Resources / 配套资源

- `scripts/diff_analyzer.py` — Diff extraction / 差异提取
- `scripts/impact_mapper.py` — Impact mapping / 影响映射
- `scripts/report_generator.py` — Report generation / 报告生成
- `references/common_patterns.md` — Conflict pattern library / 常见冲突模式库

---

## Prerequisites / 前置依赖

| Dependency / 依赖 | Purpose / 用途 | Check / 检查方式 |
|------------------|---------------|------------------|
| **Python 3.8+** | All analysis scripts | `python --version` |
| **Git** | Diff data retrieval | `git status` |
| **No third-party libs** | Standard library only | — |

AI should verify before calling scripts / AI 在调用脚本前应确认：
1. Current directory is a git repo root (`git rev-parse --show-toplevel`)
2. There are uncommitted or staged changes (`git diff --stat`)
3. Network is available (if using MCP extensions)

---

## Error Handling / 错误处理

If any script fails, AI should / 如果任何脚本执行失败，AI 应：

1. **Check environment** / 检查环境: Verify Python + Git, current directory is git repo
2. **Check changes** / 检查变更: Verify `git diff --stat` has output
3. **Fallback** / 回退策略: If scripts error, AI can manually analyze `git diff` following this SKILL.md
4. **Notify human** / 反馈人类: Report error and ask whether to continue

Common errors / 常见错误：

| Error / 错误 | Cause / 原因 | Resolution / 处理 |
|-------------|-------------|------------------|
| `Not a git repository` | Not in a git repo | Init git or switch to a repo directory |
| `json.decoder.JSONDecodeError` | Broken pipe between scripts | Re-run the full pipeline command |
| `ModuleNotFoundError` | Python environment issue | Check `python --version`, ensure >= 3.8 |

---

## Performance / 性能说明

- `impact_mapper.py` uses `grep` for project reference search; large projects (>100K files) may take 5-10s
- `grep` automatically skips `.git`, `node_modules`, `target`, `build` directories
- For performance issues, restrict scope or use `--since HEAD~1`

---

## Boundary Principles / 边界原则

1. **Not a replacement for Rules** / 不替代 Rule: Technical red lines (SQL injection prevention, security policies) are defined in `CLAUDE.md`
2. **Not a replacement for Tests** / 不替代测试: This Skill generates *business conflict analysis*, not test reports
3. **Does not block development** / 不阻塞开发: Results inform human decisions; the AI does not autonomously block changes
