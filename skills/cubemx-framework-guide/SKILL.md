---
name: cubemx-framework-guide
description: Identify the active release under docs/releases/VERSION, read its software_design.md and hardware.json, generate a concrete STM32CubeMX setup guide as docs/releases/VERSION/cubemx_build.md, verify the user-generated project framework against the documented module requirements, configure parent-workspace VS Code C/C++ settings after the framework and ARM GCC compiler are confirmed, and distinguish between guide defects and user configuration mistakes.
---

# CubeMX Framework Guide

Use this skill when Codex needs to guide the user to generate an STM32CubeMX project skeleton from existing project documents, then review the generated framework.

## Release Document Layout

Use the single-project release layout:

```text
docs/releases/<version>/
  requirements.md
  hardware.json
  software_design.md
  cubemx_build.md
  notes.md
```

If the user names a release version, use that version exactly after sanitizing it to a directory-safe name such as `v1.0`. If the user does not name a version, use the newest semantic version under `docs/releases`. If no release exists, report that the release documents are missing instead of guessing project inputs.

Read `references/guide-template.md` before drafting the CubeMX guide document.

Read `references/bionic-fish-guide-instance.md` after the template when the current task is similar to the bundled bionic fish example, or when you need a concrete example of the expected guide granularity, wording, and section depth.

Read `references/framework-checklist.md` before reviewing the generated project framework.

## Workflow

1. Identify the current project from the repository documents.
2. Read the software design document and hardware connection diagram for that project.
3. Read `references/guide-template.md` to lock the required output structure.
4. Read `references/bionic-fish-guide-instance.md` as a style and completeness reference when it is relevant.
5. Draft a concrete CubeMX setup guide and save it as `docs/releases/<version>/cubemx_build.md`.
6. Stop after the guide is delivered and wait for the user to generate the framework in CubeMX.
7. After the user says the framework is generated, inspect the produced project and verify it against the software design document.
8. If gaps exist, decide whether the guide document is incomplete or the user configuration differs from the guide, then act accordingly.
9. After the framework is confirmed usable and the ARM GCC compiler path is known and exists, configure the parent workspace `.vscode` files so VS Code can open the repository root while CMake and IntelliSense still target the generated CubeMX project.

## Project Identification

- Search `docs/releases` first.
- Prefer the active release whose directory contains both `software_design.md` and `hardware.json`.
- When multiple release directories are plausible, prefer the newest semantic version, for example `v1.0` over `v0.9`, unless the user names a version.
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
- Read module manuals under `docs/modules` only when the software design document or hardware diagram leaves a peripheral choice or parameter unclear.

## Guide Document Rules

- Save the generated guide to `docs/releases/<version>/cubemx_build.md`.
- Create `docs/releases/<version>` if it does not exist.
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
  - update the guide document at `docs/releases/<version>/cubemx_build.md`
  - explain what changed and why
  - tell the user exactly which CubeMX steps must be redone
- For a `User configuration issue`:
  - do not rewrite the whole guide unless it is ambiguous
  - point to the exact mismatched setting and the expected value
  - ask the user to correct the CubeMX configuration and regenerate if needed

## Parent Workspace VS Code Setup

- Execute this step only after:
  - the generated CubeMX/CMake framework has passed review or is explicitly accepted as usable
  - the ARM GCC compiler path has been specified and `arm-none-eabi-gcc.exe` exists
- Use this step when the user wants to open the repository parent directory in VS Code instead of opening the generated CubeMX project directory directly.
- Locate:
  - the repository parent workspace directory
  - the generated CMake project directory containing `CMakeLists.txt` or `CMakePresets.json`
  - the active build directory containing `compile_commands.json`
  - the ARM GCC compiler, normally `.../bin/arm-none-eabi-gcc.exe`
- In the parent workspace `.vscode/settings.json`, ensure these settings point at the generated project:
  - `"cmake.sourceDirectory": "<absolute generated project directory>"`
  - `"C_Cpp.default.compileCommands": "${workspaceFolder}/<generated-project>/build/<preset-or-config>/compile_commands.json"`
  - `"C_Cpp.default.compilerPath": "<absolute path to arm-none-eabi-gcc.exe>"`
  - `"C_Cpp.default.intelliSenseMode": "windows-gcc-arm"` on Windows
- In the parent workspace `.vscode/c_cpp_properties.json`, if the file exists or is already used, keep its `compileCommands` path aligned with the same `compile_commands.json`, set `compilerPath` to `arm-none-eabi-gcc.exe`, and use `windows-gcc-arm` for `intelliSenseMode` on Windows.
- Do not use host compilers such as MinGW `gcc.exe` for STM32 IntelliSense. Use the same ARM GCC family used by the CMake build.
- Preserve unrelated existing VS Code settings. Change only CMake/C_Cpp fields needed for source directory, compile commands, compiler path, and IntelliSense mode.
- After editing, verify that the JSON files parse and that both `compile_commands.json` and `arm-none-eabi-gcc.exe` exist.
- Tell the user to run `CMake: Configure` and then `C/C++: Reset IntelliSense Database` or reload VS Code.
- If STM32Cube CMake Support still warns that the parent workspace contains multiple CMake projects, explain that this is a workspace recommendation; it can be ignored when CMake and C/C++ navigation work, or avoided by opening the generated project directory directly.

## Output Rules

- Keep conclusions traceable to the software design document or hardware connection diagram.
- Separate documented facts from your inference. Label inferred items explicitly.
- When a bundled instance is used, treat it only as a formatting and completeness reference, not as evidence for the current project.
- If a required parameter cannot be derived from the available documents, say so and keep it as `TBD` instead of guessing.
- When reviewing the generated framework, report pass and fail items explicitly.
- If everything needed by the software design document is present in the generated framework, say the framework review passed and stop there.
