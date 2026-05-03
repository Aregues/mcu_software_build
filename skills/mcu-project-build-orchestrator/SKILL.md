---
name: mcu-project-build-orchestrator
description: Orchestrate the full lifecycle for a brand-new MCU, STM32, or STM32CubeMX firmware project from requirements through hardware interface, software design, CubeMX framework generation, implementation, and optional on-target debugging. Use when Codex needs to create a project from scratch, turn requirements into firmware code, generate an end-to-end new project, or establish a new versioned docs/releases release snapshot. Do not use for additions, fixes, refactors, hardware changes, or other modifications to an existing project; route those requests to project-iteration-orchestrator.
---

# MCU Project Build Orchestrator

## Overview

Use this skill as the entry point for building a new MCU or STM32CubeMX firmware project from zero. It coordinates downstream skills, enforces stage gates, and keeps project state in the existing release artifacts instead of creating a separate master plan document.

Do not use this skill for existing project changes. If the request is to add, modify, remove, fix, refactor, or change hardware in an existing MCU/CubeMX project, use `project-iteration-orchestrator` instead.

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

1. Use `requirements-doc-filling` to create `docs/releases/<version>/requirements.md`.
2. Use `hardware-interface-writer` to create `docs/releases/<version>/hardware.json`.
3. Use `software-design-doc-writer` to create `docs/releases/<version>/software_design.md`.
4. Use `cubemx-framework-guide` to create `docs/releases/<version>/cubemx_build.md`; then wait for the user to generate the CubeMX framework and review the generated skeleton.
5. Use `cubemx-code-implementation` to implement application code on top of the CubeMX-generated skeleton.
6. Use `embedded-gdb-openocd-debug` only when on-target debugging is needed and the hardware/debug environment is available.

When invoking or following downstream skills, explicitly pass the selected release directory and the outputs from completed stages.

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
