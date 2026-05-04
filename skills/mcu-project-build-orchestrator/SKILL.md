---
name: mcu-project-build-orchestrator
description: Orchestrate the full lifecycle for a brand-new MCU, STM32, or STM32CubeMX firmware project from requirements through hardware interface, software design, CubeMX framework generation, implementation, and optional on-target debugging. Use when Codex needs to create a project from scratch, turn requirements into firmware code, generate an end-to-end new project, or establish a new versioned docs/releases release snapshot. Do not use for additions, fixes, refactors, hardware changes, or other modifications to an existing project; route those requests to project-iteration-orchestrator.
---

# MCU Project Build Orchestrator

## Overview

Use this skill as the entry point for building a new MCU or STM32CubeMX firmware project from zero. It coordinates downstream skills, enforces stage gates, and keeps project state in the existing release artifacts instead of creating a separate master plan document.

Do not use this skill for existing project changes. If the request is to add, modify, remove, fix, refactor, or change hardware in an existing MCU/CubeMX project, use `project-iteration-orchestrator` instead.

## Agent Delegation Policy

The main agent must retain ownership of this orchestrator. Do not delegate `mcu-project-build-orchestrator` itself to a sub agent.

Main agent responsibilities that must not be delegated:

- stage gates and release directory selection
- user-facing confirmation, clarification, and waiting for CubeMX-generated output
- cross-stage decisions, conflict handling, and final integration
- deciding whether blocked downstream work should stop, retry, or change scope

Eligible downstream work may be dispatched to a sub agent only when its inputs are complete, its output boundary is explicit, and it can run without interactive decisions:

- `hardware-interface-writer`: may be delegated for source extraction, feasibility analysis, and a `hardware.json` draft when requirements and source files are available. Missing references, infeasible hardware, or conflicting pin/module choices must return to the main agent.
- `software-design-doc-writer`: may be delegated to draft `software_design.md` when `requirements.md` and `hardware.json` are complete and no feasibility blocker remains.
- `cubemx-framework-guide`: may be delegated to draft `cubemx_build.md` or review an already generated CubeMX skeleton. Waiting for the user to generate CubeMX output and asking the user to correct CubeMX settings remain main agent responsibilities.
- `cubemx-code-implementation`: may be delegated only for independent module drivers or independent implementation review. Business logic, HMI flow, scheduling, startup behavior, callback integration, and final application integration remain main agent responsibilities.
- `embedded-gdb-openocd-debug`: may be delegated only for complete one-shot scripted checks with known firmware artifacts, probe settings, and expected outputs. Interactive debug sessions remain main agent responsibilities.

Do not delegate `requirements-doc-filling`; it is a continuous interactive requirements collection task and must stay with the main agent.

Every sub agent task must specify the input files, expected output paths, implementation boundaries, forbidden edit areas, and required report contents. If a sub agent finds missing inputs, infeasible hardware, CubeMX/code conflicts, scope expansion, or a need for user confirmation, it must stop and report back to the main agent instead of deciding independently.

## Release Directory

Use `docs/releases/<version>` as the default document path.

When the user names a target version, use that version exactly after sanitizing it to a directory-safe name such as `v1.0`.

When the user does not name a target version:

- inspect `docs/releases`
- select the newest semantic version directory
- use `v0.1` if no historical release exists

For new projects, do not create `project_plan.md`. Use these artifacts to express project state:

```text
docs/releases/<version>/
  requirements.md
  hardware.json
  software_design.md
  cubemx_build.md
  notes.md
```

## Workflow

Run the full six-stage flow in order:

1. Main agent invokes `requirements-doc-filling` directly to create `docs/releases/<version>/requirements.md`.
2. Main agent invokes directly or dispatches eligible `hardware-interface-writer` work to a sub agent according to the delegation policy to create `docs/releases/<version>/hardware.json`.
3. Main agent invokes directly or dispatches eligible `software-design-doc-writer` work to a sub agent according to the delegation policy to create `docs/releases/<version>/software_design.md`.
4. Main agent invokes directly or dispatches eligible `cubemx-framework-guide` work to a sub agent according to the delegation policy to create `docs/releases/<version>/cubemx_build.md`; then the main agent waits for the user to generate the CubeMX framework and controls review of the generated skeleton.
5. Main agent invokes directly or dispatches eligible `cubemx-code-implementation` work to a sub agent according to the delegation policy to implement application code on top of the CubeMX-generated skeleton.
6. Main agent invokes directly or dispatches eligible `embedded-gdb-openocd-debug` checks to a sub agent according to the delegation policy only when on-target debugging is needed and the hardware/debug environment is available.

When invoking or following downstream skills, explicitly pass the selected release directory and the outputs from completed stages. When dispatching a sub agent task, also pass the exact input files, expected output paths, allowed edit scope, forbidden edit areas, stop conditions, and required report contents.

## Stage Gates

Enforce these gates before moving forward:

- Do not enter hardware interface work until `requirements.md` exists.
- Do not enter software design when the hardware is infeasible or MCU/module references are missing.
- Do not enter CubeMX guide work until `software_design.md` exists.
- Do not enter code implementation until the CubeMX project skeleton has been generated.
- Do not enter GDB/OpenOCD debugging until there is a buildable or flashable firmware artifact and a usable hardware/debug environment.

If a gate is blocked, report the missing input, ask only the focused questions needed to unblock it, and continue from the same stage after the blocker is resolved.

## Validation

Before reporting completion of a new-project build, verify as much as practical:

- the selected release directory contains the expected stage artifacts
- each downstream artifact reflects the previous stage outputs
- CubeMX framework review happened after the user generated the skeleton
- implementation changes are on top of the CubeMX skeleton rather than replacing it
- build, flash, or debug checks were run where the local environment allows
- `notes.md` or the final response records verification results and remaining risks
