# CLAUDE.md

## Project Context
- This is an STM32 firmware project built on STM32CubeMX-generated code.
- Keep the existing CubeMX project structure intact. Do not rewrite the project into a generic desktop-style layout.
- Prioritize small, local changes that preserve architecture and hardware behavior.

## Source Of Truth
- Requirements and behavior come from project docs, not guesses.
- CubeMX-generated configuration, peripheral handles, startup files, and linker settings are the hardware integration baseline.
- When requirements, design, and generated code conflict, identify the gap explicitly before implementing around it.

## Directory Ownership
- `Core/`, `Drivers/`, `Middlewares/`, startup files, linker scripts: generated or vendor-owned foundation. Edit minimally.
- `app/`: business logic, state machines, orchestration, HMI, system policy.
- `Module/`: reusable module interfaces and concrete device drivers.
- `Board/` or `board/`: hardware binding, object creation, resource injection, concrete-driver initialization.
- `Config/` or `config/`: project-level tunable parameters and feature switches.

## Dependency Rules
- `app` depends on abstract interfaces only. Do not include HAL headers or concrete driver headers in `app`.
- `Module` must not depend on `app`.
- `Board` may depend on CubeMX handles and concrete drivers, and passes abstract interfaces upward to `app`.
- Core interface headers must stay platform-neutral and must not include HAL, register, CubeMX, or board-specific headers.

## C Module Pattern
- Use object-oriented C for modules unless the project already has a stronger local convention.
- Keep a stable base interface plus wrapper functions in the core module files.
- Put the base struct as the first member of each derived struct.
- Dispatch behavior through an ops table or equivalent indirection.
- Business code uses abstract pointers only; do not cast to concrete driver types in `app`.

## CubeMX Integration Rules
- Do not move or reorganize CubeMX-generated folders.
- Prefer edits inside `USER CODE BEGIN/END` blocks and other stable extension points.
- Reuse generated handles such as `hi2c*`, `huart*`, `htim*`, DMA links, and RTOS objects instead of duplicating initialization.
- If a required peripheral, interrupt, DMA path, or middleware feature is missing, classify it as a configuration gap, design gap, or implementation gap.

## Interrupt And RTOS Rules
- Keep ISR work minimal; hand off to main loop or tasks through flags, queues, or buffers.
- Do not put business policy or heavy parsing directly in callbacks or interrupts.
- Make buffer ownership and ISR/task handoff explicit when using DMA, callbacks, or shared state.
- In RTOS projects, use APIs that are valid for the current context and avoid blocking in the wrong context.

## Configuration Rules
- Centralize timeouts, thresholds, retry counts, periods, calibration values, and feature switches under `Config`.
- Avoid magic numbers in business logic and drivers.
- Keep board-specific mapping and resource selection out of `app`.

## Change Rules
- Do not perform broad refactors unless the task explicitly requires them.
- Do not modify unrelated files.
- Do not silently mix business logic into drivers or hardware details into `app`.
- If generated files must be edited, keep the diff minimal and explain why.

## Validation And Reporting
- After changes, verify include dependencies, layer boundaries, and obvious integration issues.
- Build, syntax-check, or run available verification steps when practical; if not possible, say so explicitly.
- Report changed files, touched generated files, unresolved assumptions, and remaining risks.
