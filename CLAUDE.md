# CLAUDE.md

## Baseline

- STM32 firmware project based on STM32CubeMX-generated code. Preserve the generated layout, startup files, linker scripts, middleware, and peripheral integration.
- Requirements come from project docs and existing code. If docs, design, and generated code conflict, call out the gap before coding.
- Prefer small, local changes that preserve architecture and hardware behavior.

## Layers

- `Core/`, `Drivers/`, `Middlewares/`, startup files, linker scripts: vendor/generated foundation. Edit minimally, preferably inside stable extension points such as `USER CODE BEGIN/END`.
- `app/`: business logic, state machines, orchestration, HMI, and system policy.
- `Module/`: reusable interfaces and concrete device drivers.
- `Board/` or `board/`: hardware binding, object creation, resource injection, and concrete-driver initialization.
- `Config/` or `config/`: timeouts, thresholds, retry counts, periods, calibration values, feature switches, and board/project tunables.

## Dependency Rules

- `app` depends on abstract interfaces only; it must not include HAL, register, CubeMX, board, or concrete-driver headers.
- `Module` must not depend on `app`.
- `Board` may depend on CubeMX handles and concrete drivers, then pass abstract interfaces upward to `app`.
- Core interface headers must stay platform-neutral.
- Keep board-specific mapping and resource selection out of business logic.

## Module Style

- Use object-oriented C for modules unless the project already has a stronger local convention.
- Keep a stable base interface plus wrapper functions in core module files.
- Put the base struct first in derived structs.
- Dispatch through an ops table or equivalent indirection.
- Business code uses abstract pointers only; do not cast to concrete driver types in `app`.

## Hardware Integration

- Reuse generated handles such as `hi2c*`, `huart*`, `htim*`, DMA links, interrupts, and RTOS objects.
- If a required peripheral, interrupt, DMA path, or middleware feature is missing, classify it as a configuration gap, design gap, or implementation gap.
- Keep ISR/callback work minimal; hand off to main loop or tasks through flags, queues, buffers, or RTOS-safe APIs.
- Do not put business policy, heavy parsing, blocking calls, or invalid-context RTOS calls in interrupts/callbacks.
- Make buffer ownership and ISR/task handoff explicit when using DMA, callbacks, or shared state.

## Changes And Validation

- Do not perform broad refactors or modify unrelated files unless explicitly required.
- Do not mix business logic into drivers or hardware details into `app`.
- If generated files must be edited, keep the diff minimal and explain why.
- Avoid magic numbers outside `Config`/`config`.
- Use Conventional Commits: `<type>(<scope>): <subject>`.
- After changes, verify include dependencies, layer boundaries, and obvious integration issues.
- Build, syntax-check, or run available verification when practical; if not possible, say so.
- Report changed files, touched generated files, unresolved assumptions, and remaining risks.
