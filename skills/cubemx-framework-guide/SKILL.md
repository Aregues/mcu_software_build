---
name: cubemx-framework-guide
description: Identify the active embedded project from docs, read its software design document and hardware connection diagram, generate a concrete STM32CubeMX setup guide under docs/CubeMX_build, then verify the user-generated project framework against the documented module requirements and distinguish between guide defects and user configuration mistakes.
---

# CubeMX Framework Guide

Use this skill when Codex needs to guide the user to generate an STM32CubeMX project skeleton from existing project documents, then review the generated framework.

Read `references/guide-template.md` before drafting the CubeMX guide document.

Read `references/bionic-fish-guide-instance.md` after the template when the current task is similar to the bundled bionic fish example, or when you need a concrete example of the expected guide granularity, wording, and section depth.

Read `references/framework-checklist.md` before reviewing the generated project framework.

## Workflow

1. Identify the current project from the repository documents.
2. Read the software design document and hardware connection diagram for that project.
3. Read `references/guide-template.md` to lock the required output structure.
4. Read `references/bionic-fish-guide-instance.md` as a style and completeness reference when it is relevant.
5. Draft a concrete CubeMX setup guide and save it under `docs/CubeMX_build`.
6. Stop after the guide is delivered and wait for the user to generate the framework in CubeMX.
7. After the user says the framework is generated, inspect the produced project and verify it against the software design document.
8. If gaps exist, decide whether the guide document is incomplete or the user configuration differs from the guide, then act accordingly.

## Project Identification

- Search these locations first:
  - `docs/software_design`
  - `docs/Hardware`
  - `docs/Requirements`
- Prefer a project whose software design document and hardware connection diagram share the same project stem.
- Filenames usually follow `<project-name>-<YY-MM-DD>.<ext>`. Match by project stem first, then prefer the newest date.
- Treat the hardware connection diagram as the source of pin usage and external module wiring. It may be markdown, JSON, image-adjacent metadata, or another structured document.
- If multiple candidates are still plausible, present the ambiguity briefly and ask the user which project to use before drafting.

## Reading Strategy

- Start with the software design document to extract:
  - required software modules
  - required peripherals and communication buses
  - timing or interrupt constraints
  - RTOS or bare-metal expectations
  - storage, DMA, timer, watchdog, or debug requirements
- Then read the hardware connection diagram to extract:
  - MCU model and package
  - pin-to-module mappings
  - power, reset, boot, and debug interfaces
  - external oscillators, communication transceivers, sensors, actuators, and reserved pins
- Read module manuals under `docs/Module` only when the software design document or hardware diagram leaves a peripheral choice or parameter unclear.

## Guide Document Rules

- Save the generated guide to `docs/CubeMX_build/<project-name>-<YY-MM-DD>.md`.
- Create `docs/CubeMX_build` if it does not exist.
- Follow the structure in `references/guide-template.md`.
- Use `references/bionic-fish-guide-instance.md` as a concrete example of:
  - how much detail to provide for each CubeMX screen
  - how to separate documented facts from inferred settings
  - how to map software modules to CubeMX configuration items
- Do not copy the bundled instance mechanically into another project. Recompute every MCU, pin, peripheral, timer, DMA, and clock setting from the current project's source documents.
- Write the guide so the user can operate CubeMX step by step without inferring hidden settings.
- Include concrete values whenever the documents support them. Use `TBD` only when the source documents genuinely do not specify a value.
- For every used MCU pin, state:
  - pin name
  - CubeMX function
  - connected hardware module or signal
  - configuration notes such as pull-up, speed, interrupt edge, or default level
- For every required peripheral, state:
  - whether it must be enabled
  - operating mode
  - key parameters
  - related GPIO pins
  - interrupt and DMA expectations when applicable
- Include project-wide settings when relevant:
  - MCU selector
  - clock tree
  - SYS debug configuration
  - NVIC
  - DMA
  - middleware or RTOS
  - code generator options
  - project manager options
- End with a checklist telling the user what to verify before clicking generate.
- Do not invent middleware, tasks, queues, or code architecture that are not implied by the design documents.

## Waiting State

- After saving the guide, tell the user the file path and ask them to complete CubeMX generation.
- Do not continue into framework review until the user explicitly says the generation step is complete.

## Framework Review

- When the user says the framework is generated, inspect the newest relevant project artifacts first:
  - `*.ioc`
  - `Core/Inc`
  - `Core/Src`
  - `Drivers`
  - startup files
  - project files such as `.uvprojx`, `.project`, `.cproject`, `.ewp`, or `CMakeLists.txt`
- Use `references/framework-checklist.md` as the review checklist.
- Verify at least:
  - selected MCU matches the documents
  - all required GPIO assignments exist
  - required peripherals are enabled with plausible modes
  - interrupts and DMA are configured where the design requires them
  - clock source and core frequency satisfy design assumptions
  - generated folders and startup framework exist for later software implementation
  - no documented module is blocked by a missing CubeMX setup item

## Fault Attribution

- Classify each review issue into one of these two categories:
  - `Guide gap`: the guide document missed a required setting, wrote an ambiguous instruction, or contained a wrong recommendation.
  - `User configuration issue`: the guide was sufficient, but the generated project does not follow it.
- For a `Guide gap`:
  - update the guide document under `docs/CubeMX_build`
  - explain what changed and why
  - tell the user exactly which CubeMX steps must be redone
- For a `User configuration issue`:
  - do not rewrite the whole guide unless it is ambiguous
  - point to the exact mismatched setting and the expected value
  - ask the user to correct the CubeMX configuration and regenerate if needed

## Output Rules

- Keep conclusions traceable to the software design document or hardware connection diagram.
- Separate documented facts from your inference. Label inferred items explicitly.
- When a bundled instance is used, treat it only as a formatting and completeness reference, not as evidence for the current project.
- If a required parameter cannot be derived from the available documents, say so and keep it as `TBD` instead of guessing.
- When reviewing the generated framework, report pass and fail items explicitly.
- If everything needed by the software design document is present in the generated framework, say the framework review passed and stop there.
