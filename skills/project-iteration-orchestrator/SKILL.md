---
name: project-iteration-orchestrator
description: Orchestrate incremental iterations for an existing MCU or STM32CubeMX project by creating and confirming an Engineering Change Request before downstream documents or code change. Use when Codex needs to handle additions, modifications, removals, bug fixes, refactors, hardware changes, compatibility changes, or other iteration requests based on existing project code, an existing CubeMX project, or existing docs/releases/VERSION artifacts.
---

# Project Iteration Orchestrator

## Overview

Use this skill to control changes to an existing MCU project as a versioned iteration. Start by creating an ECR under `docs/releases/<next-version>/ecr.md`; do not proceed to full requirements, hardware, CubeMX framework, or code work until the user confirms the ECR.

This skill orchestrates existing skills. It does not replace their detailed workflows.

## Version Selection

Use `docs/releases/<version>` as the release document layout.

When the user names a target version, use that version exactly after sanitizing it to a directory-safe name such as `v1.0`.

When the user does not name a target version:

- inspect `docs/releases`
- select the newest semantic version directory
- increment the last numeric component for the next version
- use `v0.1` if no historical release exists

Examples:

- `v0.1` -> `v0.2`
- `v1.2.3` -> `v1.2.4`
- no release directory -> `v0.1`

## ECR First

Create `docs/releases/<next-version>/ecr.md` before creating or changing any downstream artifact. The ECR must contain exactly these top-level sections:

```markdown
# ECR - <next-version>

## 1. 需求描述
<基于用户原始描述整理；信息不足时通过问答补齐。>

## 2. 影响分析
<模型自主分析对需求文档、硬件连接、软件设计、CubeMX 配置、代码、测试和兼容性的影响。>

## 3. 决策结果
<模型整理可行方案、推荐方案、取舍理由，以及需要用户确认的最终决策。>

## 4. 实施约束
<模型列出增量/减量修改边界、禁止重建范围、CubeMX 保护规则、兼容性约束、测试约束。>

## 5. 验收结果
<初始为“待验收”；实现和验证完成后记录验收项、验证结果、遗留问题。>
```

Use the user's original request as the source for `## 1. 需求描述`. Ask focused clarification questions only when a missing decision would change scope, hardware wiring, safety behavior, compatibility, or implementation boundaries.

In `## 2. 影响分析`, independently analyze impact on:

- `requirements.md`
- `hardware.json`
- `software_design.md`
- `cubemx_build.md`
- CubeMX `.ioc` configuration and generated framework
- application code, module drivers, board binding, and configuration
- tests, build checks, flashing/debugging, and backward compatibility

In `## 3. 决策结果`, list feasible options, the recommended option, tradeoffs, and concrete decisions that need user confirmation.

In `## 4. 实施约束`, state the incremental boundary clearly:

- only add, modify, or delete content required by the ECR
- do not rebuild the project from scratch
- do not rearrange CubeMX-generated directories
- do not overwrite user-owned implementation unless the ECR explicitly requires it
- keep manual CubeMX edits inside stable user extension points when possible
- preserve compatibility unless the ECR explicitly accepts a breaking change
- record conflicts before changing documents, CubeMX configuration, or code

Initialize `## 5. 验收结果` as `待验收`. After implementation and verification, update it with acceptance items, verification results, and known remaining issues.

## Confirmation Gate

Do not enter full requirements-document, hardware-connection, framework, or code stages until the user confirms the ECR decisions.

Before confirmation, allowed work is limited to:

- inspect existing documents and code to understand impact
- create or revise `ecr.md`
- ask clarifying questions
- report conflicts, missing inputs, and recommended decisions

If existing documents, hardware wiring, CubeMX configuration, or code conflict with the ECR, record the difference in the ECR and ask for confirmation before resolving the conflict.

## Iteration Workflow

After the user confirms the ECR, generate or update artifacts in the same new release directory:

```text
docs/releases/<next-version>/
  ecr.md
  requirements.md
  hardware.json
  software_design.md
  cubemx_build.md
  notes.md
```

Use or follow the existing skills in this order as applicable:

1. Use `requirements-doc-filling` for `docs/releases/<next-version>/requirements.md`.
2. Use `hardware-interface-writer` for `docs/releases/<next-version>/hardware.json`.
3. Use `software-design-doc-writer` for `docs/releases/<next-version>/software_design.md`.
4. Use `cubemx-framework-guide` for `docs/releases/<next-version>/cubemx_build.md` and CubeMX framework review.
5. Use `cubemx-code-implementation` for incremental software implementation on the existing CubeMX project.

When invoking or following downstream skills, explicitly carry forward the ECR constraints and require incremental work. A full document may describe the complete target behavior for the new release, but framework and code changes must be limited to the delta needed for this iteration.

## Incremental Implementation Rules

For documents, describe the complete new-version behavior while preserving traceability to the previous release and ECR.

For hardware, CubeMX, and code:

- inspect existing files before changing them
- prefer narrow additions and local modifications
- keep existing folder structure and established architecture
- preserve CubeMX-generated layout and user code blocks
- avoid unrelated refactors, formatting churn, or generated metadata churn
- ask before deleting behavior that may be user-owned or compatibility-relevant

## Validation

Before reporting completion of an iteration, verify as much as practical:

- `ecr.md` exists and records the confirmed decisions
- downstream artifacts are in the same `docs/releases/<next-version>` directory
- code and CubeMX changes match the incremental scope in `## 4. 实施约束`
- build, static checks, or manual verification steps were run where available
- `## 5. 验收结果` records verification results and remaining risks
