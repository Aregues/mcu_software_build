# mcu_go

面向 Claude Code 和 Codex 的 MCU 嵌入式软件开发插件，用于支持 STM32 / ARM Cortex-M 项目从需求收集到板上调试的完整开发流程，尤其适合基于 STM32CubeMX 生成工程框架的项目。

## 技能列表

| 技能 | 命令 | 说明 |
|------|------|------|
| mcu-project-build-orchestrator | `/mcu-project-build-orchestrator` | 面向全新 MCU/CubeMX 项目的全生命周期编排入口 |
| project-iteration-orchestrator | `/project-iteration-orchestrator` | 面向已有 MCU/CubeMX 项目的 ECR 优先增量迭代编排入口 |
| requirements-doc-filling | `/requirements-doc-filling` | 交互式收集项目需求，并生成结构化 SRS 需求文档 |
| hardware-interface-writer | `/hardware-interface-writer` | 分析 MCU 引脚和模块手册，并编写硬件连接 JSON |
| software-design-doc-writer | `/software-design-doc-writer` | 基于需求文档和硬件连接信息自动生成软件设计文档 |
| cubemx-framework-guide | `/cubemx-framework-guide` | 生成 CubeMX 配置步骤指南，并检查生成后的工程框架 |
| cubemx-code-implementation | `/cubemx-code-implementation` | 在 CubeMX 生成的工程骨架上实现完整应用代码 |
| embedded-gdb-openocd-debug | `/embedded-gdb-openocd-debug` | 使用 OpenOCD 和 arm-none-eabi-gdb 调试 STM32 固件 |

## 推荐工作流

本插件提供两个主要工作流入口：全新项目创建和已有项目迭代。

### 创建全新项目

当用户希望从零创建 MCU、STM32 或 CubeMX 固件项目，或者需要从需求开始一直生成到代码时，先使用全新项目编排器：

```text
1. /mcu-project-build-orchestrator
2. /requirements-doc-filling    -> docs/releases/<version>/requirements.md
3. /hardware-interface-writer   -> docs/releases/<version>/hardware.json
4. /software-design-doc-writer  -> docs/releases/<version>/software_design.md
5. /cubemx-framework-guide      -> docs/releases/<version>/cubemx_build.md -> 用户在 CubeMX 中生成工程 -> 复查
6. /cubemx-code-implementation  -> 基于 CubeMX 工程骨架生成 app/ 和 Module/ 代码
7. /embedded-gdb-openocd-debug  -> 在需要时进行板上调试
```

`/mcu-project-build-orchestrator` 适用于以下场景：

- 创建全新的 MCU/STM32/CubeMX 固件项目
- 从需求到代码生成端到端项目
- 建立新的 `docs/releases/<version>` 版本快照

全新项目编排流程固定包含以下六个阶段：

```text
1. /requirements-doc-filling    -> docs/releases/<version>/requirements.md
2. /hardware-interface-writer   -> docs/releases/<version>/hardware.json
3. /software-design-doc-writer  -> docs/releases/<version>/software_design.md
4. /cubemx-framework-guide      -> docs/releases/<version>/cubemx_build.md -> 用户在 CubeMX 中生成工程 -> 复查
5. /cubemx-code-implementation  -> 基于 CubeMX 工程骨架生成 app/ 和 Module/ 代码
6. /embedded-gdb-openocd-debug  -> 板上调试会话
```

### 迭代已有项目

当用户希望在已有 MCU/CubeMX 项目中新增、修改、删除、修复、重构功能，或调整硬件连接时，先使用迭代编排器：

```text
1. /project-iteration-orchestrator -> docs/releases/<next-version>/ecr.md
2. 与用户确认 ECR 决策
3. 生成或更新 docs/releases/<next-version>/requirements.md
4. 按需生成或更新 hardware.json、software_design.md、cubemx_build.md
5. 仅应用 ECR 所要求的增量 CubeMX 或代码变更
6. 在 ecr.md 中记录验证结果和验收结论
```

`/project-iteration-orchestrator` 会让迭代工作先经过 ECR 控制，避免下游技能在没有确认的情况下重建项目或覆盖已有实现。

## 项目文档布局

本插件假设一个仓库对应一个 MCU 项目。项目交付物以 release 快照形式进行版本化管理：

```text
docs/
|-- releases/
|   |-- v0.1/
|   |   |-- ecr.md
|   |   |-- requirements.md
|   |   |-- hardware.json
|   |   |-- software_design.md
|   |   |-- cubemx_build.md
|   |   `-- notes.md
|   `-- v1.0/
|       |-- requirements.md
|       |-- hardware.json
|       |-- software_design.md
|       |-- cubemx_build.md
|       `-- notes.md
|-- modules/
|   `-- <module-name>/
|       |-- manual.md
|       `-- source files such as PDFs or images
`-- mcu/
    `-- pin-definition source files and converted markdown
```

未指定版本时，`/mcu-project-build-orchestrator` 和其它全新项目技能会使用 `docs/releases` 下最新的语义化版本；如果不存在任何历史版本，则创建 `docs/releases/v0.1`。

已有项目迭代时，`/project-iteration-orchestrator` 会基于最新语义化版本递增最后一个数字段来创建下一个版本，例如 `v0.1` -> `v0.2`，或 `v1.2.3` -> `v1.2.4`。如果没有历史版本，则从 `v0.1` 开始。

## 安装

将 `mcu_go` 文件夹放入 Claude Code 工作区，或使用以下命令安装：

```bash
claude plugin add /path/to/mcu_go
```

## 项目结构

```text
mcu_go/
|-- .codex-plugin/plugin.json            # Codex 插件清单
|-- .claude-plugin/plugin.json           # Claude 插件清单
|-- README.md
`-- skills/
    |-- mcu-project-build-orchestrator/  # 全新项目编排器：完整生命周期
    |   |-- SKILL.md
    |   `-- agents/openai.yaml
    |-- project-iteration-orchestrator/  # 迭代编排器：ECR 优先变更
    |   |-- SKILL.md
    |   `-- agents/openai.yaml
    |-- requirements-doc-filling/        # 技能 1：需求收集
    |   |-- SKILL.md
    |   |-- agents/openai.yaml
    |   `-- references/
    |-- hardware-interface-writer/       # 技能 2：硬件接口分析
    |   |-- SKILL.md
    |   |-- agents/openai.yaml
    |   |-- references/
    |   `-- scripts/pdf_to_md.py
    |-- software-design-doc-writer/      # 技能 3：软件设计文档
    |   |-- SKILL.md
    |   |-- agents/openai.yaml
    |   `-- references/
    |-- cubemx-framework-guide/          # 技能 4：CubeMX 配置指南
    |   |-- SKILL.md
    |   |-- agents/openai.yaml
    |   `-- references/
    |-- cubemx-code-implementation/      # 技能 5：代码实现
    |   |-- SKILL.md
    |   |-- agents/openai.yaml
    |   `-- references/
    `-- embedded-gdb-openocd-debug/      # 技能 6：GDB/OpenOCD 调试
        |-- SKILL.md
        |-- agents/openai.yaml
        `-- references/
```

## 环境要求

- Python 3：用于 `hardware-interface-writer` 中的 `pdf_to_md.py`
- ARM GCC 工具链：例如 `arm-none-eabi-gcc`，用于构建验证
- OpenOCD 和 ST-Link：用于板上调试
- STM32CubeMX：用于生成工程框架

## 许可证

专有软件。保留所有权利。
