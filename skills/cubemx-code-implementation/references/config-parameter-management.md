# Configuration Parameter Management

Read this file when the task needs parameter layout, parameter injection, or review of scattered embedded project parameters.

## Goal

Keep project-tunable parameters centralized, traceable, and aligned with the software design document while preserving the dependency boundaries between `app`, `Board`, and `Module`.

Use this convention:

- project-centralized configuration in a top-level `Config` or `config` directory
- board binding maps project configuration into concrete object initialization
- modules keep only module-local constants and reusable defaults
- business `app` code owns policy and state machines, not project-wide configuration plumbing

## Placement Rules

### Project-Level Tunable Parameters

Store project-tunable parameters in a dedicated top-level file such as `Config/project_config.h` or `config/project_config.h`.

Typical examples:

- business thresholds
- control gains or setpoints
- timeout values
- retry counts
- task periods
- queue depths when they are selected by project design
- RTOS stack sizes when they are selected by project design
- calibration values
- feature enable switches
- default degraded-mode behavior

Even if a parameter affects only one module, keep it in the project configuration layer when the project may tune it.

Do not make `app/app_config.h` the default project-wide configuration hub. Use `app/app_config.h` only for business-layer private settings when the existing project already has that convention or the design explicitly requires it.

### Board Binding Configuration

Board binding files under `Board` or `board` may include the project configuration header and concrete driver headers.

Board binding is the preferred place to:

- translate project configuration macros into concrete driver config structs
- pass CubeMX handles, GPIO ports, pins, timer channels, bus handles, DMA buffers, and calibration values to concrete init functions
- keep concrete object allocation private
- expose only abstract base pointers or board-level abstract accessors to `app`

Do not put board binding configuration in `app`, and do not create project-resource binding headers inside `Module`.

### Module-Local Contents

Keep these in the owning `Module`:

- register addresses
- chip limits from the datasheet
- protocol frame markers
- CRC constants
- local parsing limits
- compile-time capability bounds that are part of the module implementation
- internal fallback defaults for reusable standalone drivers

Do not expose module-internal constants in the project configuration layer unless the software design explicitly treats them as project-tunable.

## Injection Rules

When a concrete driver needs configurable behavior, use one of these patterns:

- config struct passed at init
- explicit init arguments
- narrow macro mapping in `Board` from `Config/project_config.h` to a driver config struct

Prefer explicit config structs when a driver has several related tunables. Prefer direct named init arguments when only one or two values are injected.

Core interface headers must not include project configuration headers. Concrete drivers should not include broad project configuration headers unless there is a documented reuse tradeoff; prefer injection through init/config structs.

Do not let modules read scattered project parameters from many unrelated headers.

## Naming Rules

- Prefix project-level configuration names with `PROJECT_`, `CFG_`, or another existing project-wide prefix.
- Add subsystem or module grouping to the name, for example:
  - `PROJECT_CTRL_LOOP_PERIOD_MS`
  - `PROJECT_COMM_UART_RETRY_COUNT`
  - `PROJECT_SENSOR_UART_TIMEOUT_MS`
  - `PROJECT_FREERTOS_CONTROL_TASK_STACK_WORDS`
- Include units in the macro name when practical.
- If the unit is not in the name, document it adjacent to the declaration.
- Avoid unnamed literals in code paths that represent tunable policy.

If the existing project already uses `APP_` for project-wide values, keep consistency but do not let that naming imply that drivers may depend on `app` headers.

## Default and Override Rules

- `Config/project_config.h` or the existing top-level project configuration header is the project's single source of truth for tunable values.
- A module may define local fallback defaults only when the module is designed to be reusable in isolation, and the fallback behavior is clearly documented.
- If both project and module defaults exist, the project-level value must be the active one in the integrated application.
- Do not create separate project-level `*_config.h` files inside each module folder as an informal override system.
- Do not create multiple competing project configuration hubs unless the software design explicitly defines ownership and include direction.

## TBD Handling

- If a threshold, timeout, retry count, calibration value, queue depth, or stack size is not yet confirmed, put a `TBD` marker or clearly named temporary placeholder in the project configuration layer.
- Do not hide unresolved values as unexplained magic numbers in implementation files.
- Keep temporary assumptions easy to review and replace.

## Forbidden Patterns

- scattered project tunables across multiple unrelated headers
- project timeout or retry values hard-coded in driver source
- per-module project config headers created without an explicit architecture decision
- module code owning business thresholds
- core interface headers including project configuration headers
- concrete drivers depending on broad `app` headers just to obtain parameters
- board-resource binding or project configuration mapping placed inside `app` business code
- RTOS task timing and stack values hidden only in task source without project-level traceability

## Review Checklist

Check these before accepting code:

- project-tunable parameters are centralized in a top-level project configuration header such as `Config/project_config.h`
- board binding maps project configuration into concrete driver init/config structs
- module constants and project tunables are not mixed together carelessly
- names and units are clear
- tunable values are traceable to requirements or software design intent
- modules receive tunables through explicit interfaces or documented narrow mapping
- core interface headers do not include project configuration headers
- no unexplained magic numbers remain for thresholds, timeouts, retries, calibration values, task periods, queue depths, or stack sizes
