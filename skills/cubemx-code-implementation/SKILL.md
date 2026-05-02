---
name: cubemx-code-implementation
description: Implement, build, verify, or flash a complete embedded application on top of an STM32CubeMX-generated framework by using the generated requirement document, software design document, CubeMX setup guide, and project skeleton. Use when Codex needs to work in a CubeMX project, including CMake/Ninja projects with `CMakePresets.json`, `cmake/gcc-arm-none-eabi.cmake`, OpenOCD flashing, adding `Common`, `app` or `APP`, `Module`, `Board`, and `Config` implementation code without breaking CubeMX-generated directory structure, parallelizing unrelated module-driver work with subagents, and keeping business logic and HMI code in the main agent for user-facing clarification.
---

# CubeMX Code Implementation

Use this skill to turn project documents plus an STM32CubeMX-generated project skeleton into working embedded code.

Read project documents directly from the active release under `docs/releases/<version>`:

- requirement document at `docs/releases/<version>/requirements.md`
- software design document at `docs/releases/<version>/software_design.md`
- CubeMX setup guide or framework review notes at `docs/releases/<version>/cubemx_build.md`
- optional implementation notes at `docs/releases/<version>/notes.md`
- shared module manuals under `docs/modules`

Treat these `docs` artifacts as the implementation basis. Do not depend on re-reading upstream skill definitions when the needed project information is already present in `docs`.

If the user names a release version, use that version exactly after sanitizing it to a directory-safe name such as `v1.0`. If the user does not name a version, use the newest semantic version under `docs/releases`. If no release exists, report that the required release documents are missing instead of guessing project inputs.

## Module Manual Lookup Rules

When implementing or reviewing a module driver, locate its manual under `docs/modules/<module-name>`, where `<module-name>` should match the module being implemented as closely as the repository naming allows.

Inside the module-named folder, prefer markdown files first. The markdown manual is a converted and merged version of the module's source manual files, so read it before PDFs, images, or other original source artifacts. If multiple markdown files exist, start with the broadest manual-style file such as `manual.md`, `README.md`, or the file whose name matches the module folder, then read narrower markdown supplements only when needed.

Use PDFs or other original artifacts only when the relevant detail is missing, ambiguous, or contradicted in the markdown manual. If the module-named folder or merged markdown manual is missing, report that as a documentation gap before treating the driver behavior as fully specified.

## Reference Files

Load these references only when their condition applies:

- `references/embedded-development-rules.md`: read before writing or reviewing capability interface files, concrete drivers, board binding files, business application code, or CubeMX user-code blocks.
- `references/config-parameter-management.md`: read when adding, injecting, centralizing, or reviewing timeouts, thresholds, retry counts, calibration values, queue depths, stack sizes, task periods, or feature switches.
- `references/peripheral-callback-rules.md`: read when using interrupts, HAL callbacks, DMA, polling loops, shared buffers, or ISR-to-main/task handoff.
- `references/freertos-development-rules.md`: read when the CubeMX project includes FreeRTOS middleware or RTOS-generated source files.
- `references/watchdog-safe-startup-rules.md`: read when requirements, software design, CubeMX configuration, or generated code includes IWDG, WWDG, reset-cause handling, startup self-checks, or safe-startup behavior.
- `references/object-oriented-c-module-architecture.md`: read when designing, implementing, or reviewing module interfaces, concrete drivers, board binding, or business-layer dependencies.
- `references/subagent-implementation-and-review.md`: read before dispatching or reviewing subagents for independent module-driver work.
- `references/automated-review-checks.md`: read before reviewing completed implementation work, subagent output, or suspected style violations; run the documented grep-based checks before final manual review when practical.
- `references/cmake-build-and-openocd-flash.md`: read when the CubeMX project is a CMake/Ninja project, has `CMakePresets.json`, uses `cmake/gcc-arm-none-eabi.cmake`, or the user asks to build, verify, or flash firmware with CMake, Ninja, ARM GCC, or OpenOCD.

When dispatching a subagent, explicitly name the reference files it must read. Do not assume the subagent will infer these rules from this skill.

## Required Inputs

- One requirement document at `docs/releases/<version>/requirements.md`
- One software design document at `docs/releases/<version>/software_design.md`
- Optionally one CubeMX guide or framework review note at `docs/releases/<version>/cubemx_build.md`
- One generated STM32CubeMX project tree containing at least:
  - `*.ioc`
  - `Core`
  - `Drivers`

If multiple candidate projects exist, match by shared project stem first and then prefer the newest date.

## Core Objective

Generate the full project code required by the requirement document and software design document on top of the existing CubeMX framework.

Implement under the CubeMX project rather than as a standalone rewrite. Keep the CubeMX-generated directory structure intact and add implementation code through the top-level `Common`, `app` or `APP`, `Module`, `Board` or `board`, and `Config` or `config` folders as needed.

When designing or implementing a module, use object-oriented C design unless the existing project already has a stronger local convention. The CubeMX-generated project remains the base framework; object boundaries are added on top of it and must not require reorganizing CubeMX output.

The main architecture rule is: upper layers depend on capability interfaces, not on a specific hardware implementation. For example, an MPU6050 driver depends on an I2C register-access interface, not directly on `hi2c1`, `GPIOB`, `HAL_I2C_Mem_Read`, or an `i2c_hal` concrete driver.

## Reading Strategy

Read artifacts in this order:

1. Requirement document: extract project goals, functional requirements, non-functional constraints, HMI behavior, exception paths, and module interactions.
2. Software design document: extract software layers, module boundaries, runtime flow, task periods, interrupts, interfaces, data ownership, and fault handling.
3. CubeMX guide or generated framework review notes: extract intended peripherals, pin assignments, timers, DMA, communication buses, and known framework gaps.
4. Generated project tree: inspect `*.ioc`, `Core/Inc`, `Core/Src`, `Drivers`, middleware folders, and build files to determine actual integration points.
5. `docs/modules`: read only the module-named folders relevant to modules being implemented, following the Module Manual Lookup Rules and preferring the converted merged markdown manual before PDFs or original source artifacts.
6. Load the reference files listed above according to the project features and implementation work.

## CubeMX Integration Rules

- Treat CubeMX output as the base framework.
- Do not move, delete, or reorganize CubeMX-generated folders such as `Core`, `Drivers`, startup files, linker scripts, or project files.
- Prefer adding:
  - `Common` for cross-module capability interfaces, shared status values, and platform-neutral utilities
  - `app` for business logic, state machines, HMI flow, orchestration, and project-level services
  - `Module` for reusable external-device drivers or hardware abstractions
  - `Board` or `board` for object creation, CubeMX resource binding, concrete-driver initialization, and abstract accessors
  - `Config` or `config` for centralized project-tunable parameters
- If generated files must be touched, restrict manual edits to stable extension points first:
  - `/* USER CODE BEGIN ... */` and `/* USER CODE END ... */` blocks
  - user-owned include lists
  - project build files only when needed to include new source folders
- Use generated handles such as `hi2c*`, `huart*`, `htim*`, DMA links, IWDG/WWDG handles, and generated init paths instead of duplicating peripheral initialization.
- Prefer HAL/CubeMX-provided APIs and patterns before writing custom low-level infrastructure. Do not reimplement behavior already provided by HAL, such as UART DMA reception with idle detection; use the relevant HAL receive-to-idle DMA APIs and callbacks when the installed HAL package supports them, and only fall back to custom IRQ/DMA glue after confirming the HAL version or generated framework lacks the needed support.
- Keep startup wiring simple and explicit:
  - initialization entry in `main.c` user blocks or a dedicated app init call
  - periodic service in the main loop, timer callbacks, or RTOS tasks according to the design document
  - interrupt-related handoff through generated callback hooks or user sections
- If the framework lacks a required peripheral, DMA path, interrupt, pin assignment, clock assumption, watchdog, or middleware feature, stop and classify the gap as:
  - framework/configuration gap
  - design/document gap
  - implementation gap

## Program Architecture Constraints

Use the `Common` / `Module` / `APP` or `app` / `Board` layering model. The goal is not to create extra folders for their own sake; it is to keep changes localized when pins, bus implementations, device models, boards, or business policies change.

- `Common` owns capability interfaces and platform-neutral shared code: `status.h`, `error.h`, `i2c_if.h`, `spi_if.h`, `uart_if.h`, `display_if.h`, `led_if.h`, ring buffers, CRC helpers, and similar utilities.
- `Common` must not contain current-board pin configuration, CubeMX handles such as `hi2c1` or `huart1`, HAL calls, register access, concrete driver headers, board headers, or `app` business types.
- `Module` owns hardware capabilities and reusable modules:
  - `Module/bus` implements bus or MCU peripheral behavior such as HAL I2C, GPIO I2C, SPI, UART, PWM, ADC, or timers; it may depend on HAL/CubeMX because it is the concrete platform adapter.
  - `Module/device` owns a concrete external device or chip protocol such as MPU6050, SSD1306, or W25Q64; it may know registers and data formats, but must not know product business states or which concrete bus implementation is used.
  - `Module/component` combines abstract interfaces into a higher-level reusable feature such as display, status LED, button manager, storage, or sensor fusion; it should prefer `Common/*_if.h` interfaces over concrete device headers.
- `APP` or `app` owns product behavior: state machines, events, control policy, HMI flow, inter-module coordination, scheduling, and system-level health decisions.
- `APP` or `app` must not own low-level operations such as GPIO toggling, I2C/SPI/UART register transfers, OLED controller command details, sensor register parsing, CubeMX handle selection, or board pin mapping.
- `Board` or `board` is the only layer that knows which device is wired to which pins, bus handles, DMA channels, timer channels, addresses, chip-select lines, and concrete implementations.
- `Board` or `board` creates concrete objects, injects CubeMX resources, selects implementations such as hardware I2C versus GPIO-simulated I2C, calls concrete init functions, and exposes only abstract capability pointers or narrow board-level services upward.
- Keep board binding in a dedicated top-level directory such as `Board` or `board`, at the same level as `Common`, `app`, and `Module`; do not place board binding inside concrete driver folders and do not mix it into the business `app` directory.
- Preserve dependency direction:
  - CubeMX/HAL generated layer provides the hardware access foundation.
  - `Common/*_if.h` defines stable capability interfaces only.
  - `Module/device` and `Module/component` use `Common/*_if.h` interfaces instead of concrete hardware implementations.
  - `Module/bus` and concrete drivers implement capability interfaces using HAL/CubeMX or low-level hardware libraries.
  - `Board` or `board` binds concrete implementations and CubeMX resources, then hands abstract pointers to `app`.
  - `APP` or `app` uses abstract interfaces and project-level services only.
- If the existing project already has a capability-interface directory inside `Module`, keep the local convention, but enforce the same boundary as `Common`: no HAL, CubeMX, board, GPIO, PWM, I2C, SPI, UART, DMA, timer, register, concrete-driver, or business dependency leaks.
- Do not let business rules leak into device drivers, and do not let device register details leak upward into `app` unless the software design explicitly requires that exposure.
- If project configuration must flow into a driver, prefer a top-level `Config/project_config.h` pattern plus config structs, init arguments, or explicit narrow mapping in board binding as described in `references/config-parameter-management.md`.
- Separate `construct` from `init` when the module owns persistent objects: `construct` binds function pointers and dependency references; `init` performs hardware communication, register configuration, buffer clearing, sampling start, display start, or other actions that may need retry or deinit/reinit.

Typical dependency chain:

```text
APP/app
  -> Module/component or Module/device through abstract APIs
  -> Common/*_if.h capability interfaces
  <- Module/bus or concrete device implementations
  <- Board selects concrete implementations and injects CubeMX resources
```

These are automatic violations unless the design explicitly names a controlled exception:

```text
HAL headers, generated hardware headers, GPIO ports/pins, timer handles,
DMA handles, hi2c/huart/hspi/htim handles, concrete driver headers,
SSD1306 page-address commands, MPU6050 register-transfer details, or
HAL_GPIO_WritePin/HAL_I2C_Mem_Read calls in APP/app code.
```

## Object-Oriented C Module Architecture

Read `references/object-oriented-c-module-architecture.md` for the full pattern, examples, and review checklist when practical. If that reference is not loaded, still follow these minimum rules:

- split each module into a capability interface layer, concrete driver layer, board binding layer, and business application layer
- put stable abstract APIs in `Common/*_if.h` or the project's established capability-interface location: base struct, ops table, status enum, capability flags when needed, and wrapper functions
- put hardware-specific derived types in files such as `xxx_gpio.h/.c`, `xxx_pwm.h/.c`, or `xxx_i2c.h/.c`
- put the base struct as the first member of every derived struct, bind a `static const xxx_ops_t` table during init, and call behavior through wrapper functions
- keep `app` code on abstract pointers such as `xxx_base_t *`; do not cast to concrete types or branch on concrete driver kind
- let files under `Board` or `board` create concrete objects, inject CubeMX resources, call concrete init functions, and pass only abstract base pointers to `app`
- keep capability interface headers free of HAL, register, CubeMX, board, GPIO, PWM, I2C, SPI, UART, DMA, timer, and concrete-driver dependencies
- use capability queries or extension interfaces for optional behavior instead of expanding the base interface for one device variant
- when asked for module architecture output, include recommended file structure, file responsibilities, include relationships, capability struct design, init and board-binding flow, business call example, dependency explanation, and common wrong patterns

## Implementation Workflow

1. Identify the active project and exact CubeMX project root.
2. Confirm the generated framework is present and roughly consistent with the design document.
3. Load applicable reference files before implementation.
4. Build an implementation plan grouped by:
   - external module drivers
   - board binding
   - project configuration
   - application services
   - business logic and HMI flow
5. Create `Common`, `app` or `APP`, `Module`, `Board` or `board`, and `Config` or `config` folders as required by the implementation if they do not already exist.
6. For unrelated external-module drivers, prepare parallel subagent tasks with explicit ownership and required reference files.
7. Implement unrelated external-module drivers under `Module`.
8. Review subagent work before integration; require rewrite for confirmed violations rather than silently adapting broken code.
9. Integrate accepted drivers through board binding with CubeMX handles, board resources, and project configuration.
10. Implement application orchestration, business rules, and HMI behavior under `app`.
11. Connect startup, periodic scheduling, interrupt callbacks, or polling loops through allowed CubeMX integration points.
12. Build or run available checks when practical.
13. Report generated files, touched generated files, unresolved assumptions, and user decisions still needed.

## Parallelization Rules

Use subagents only for independent module-driver tasks.

Good subagent candidates:

- one sensor driver under `Module/<sensor-name>`
- one communication module driver under `Module/<radio-name>`
- one power-monitor driver under `Module/<power-monitor-name>`

Do not delegate tasks involving:

- business rules
- user interaction flow
- HMI state or display flow
- ambiguous requirement interpretation
- cross-module orchestration
- edits to shared startup flow or shared callback dispatch
- unresolved architectural tradeoffs that may require user confirmation

These stay in the main agent so clarification and product behavior decisions remain centralized.

## Subagent Task Requirements

Read `references/subagent-implementation-and-review.md` before dispatching implementation subagents. At minimum, each subagent task must define a narrow owned module area, state that the subagent must not revert others' changes, require the relevant docs and references, keep board binding out of `Module`, and prohibit changes to business logic, HMI flow, shared startup, unrelated callbacks, or unrelated framework files.

## Subagent Review Requirements

Read `references/subagent-implementation-and-review.md` before reviewing subagent output. At minimum, run automated checks when practical, explicitly judge every hit, verify ownership boundaries, confirm board binding is in a dedicated top-level `Board` or `board` directory, confirm capability interfaces are platform-neutral, and require rewrite for confirmed violations before integration.

## Main-Agent Responsibilities

The main agent owns:

- project-level architecture decisions
- requirement interpretation
- business workflows
- HMI code and interaction sequencing
- cross-module scheduling and arbitration
- safety behavior and degraded-mode policy
- edits to shared startup flow or shared callback dispatch
- all user communication about unclear product behavior

When requirement or design artifacts leave business behavior uncertain, stop at the uncertainty, name it concretely, and ask the user instead of guessing.

## Validation Rules

Before claiming completion, verify as many of these as practical:

- every major requirement is mapped to code ownership
- every required external module has a concrete implementation or explicit blocker
- `Common`, `app` or `APP`, `Module`, `Board` or `board`, and `Config` or `config` integration points are connected to the CubeMX framework
- edited generated files still preserve CubeMX structure and user sections
- automated review checks have been run for completed implementation or subagent output when practical, and all hits are explained or corrected
- major tunable parameters are centralized and traceable
- DMA, interrupt, callback, RTOS, and watchdog behavior follow the applicable reference files
- periodic, interrupt, and communication paths are consistent with the software design
- obvious compile-time integration issues such as missing includes, duplicate symbols, or unreferenced handles are addressed

### CubeIDE and ARM GCC Build Verification Flow

When the project uses an STM32CubeIDE `.cproject` and new source folders or module subfolders were added, treat this as the default verification flow:

1. Update the CubeIDE project metadata before building:
   - add each new public include directory to every relevant C compiler include path group in `.cproject`
   - include capability interface directories such as `Common` or `Module/<module-name>`, concrete driver directories when their headers are used by board binding, dedicated board binding directories such as `Board`, project configuration directories such as `Config`, and `app` directories that expose business application headers
   - add new source roots such as `Common`, `app`, `Board`, `Module`, or specific module subfolders to each relevant `<sourceEntries>` group; add `Config` include paths when it contains headers
   - preserve existing CubeMX-generated source roots such as `Core` and `Drivers`
   - do not edit `.cproject` for unrelated toolchain or optimization churn
2. Run an ARM GCC syntax-only check when `arm-none-eabi-gcc` is available:
   - include `Core/Inc`, capability interface headers, concrete driver headers needed by board binding, `Board` headers, `Config` headers, `app` headers, HAL driver headers, CMSIS device headers, and CMSIS core headers
   - use the MCU flags from the CubeMX project, for example Cortex-M4 Thumb hard-float flags for STM32F407
   - define required CubeMX/HAL symbols such as `USE_HAL_DRIVER` and the exact device macro such as `STM32F407xx`
   - compile implementation-owned C files with `-fsyntax-only` first, grouped as capability interface wrappers, concrete drivers, board binding, and business application files
   - syntax-check capability interface files with only platform-neutral include paths when practical, to catch accidental HAL, CubeMX, board, or concrete-driver dependency leaks
3. Run a full compile check when practical:
   - compile capability interface wrappers, concrete drivers, board binding, business application files, `Core/Src`, and the required `Drivers/STM32F4xx_HAL_Driver/Src` C files into temporary object files under a local build-verification directory such as `build_verify`
   - compile the CubeMX startup assembly file, for example `Core/Startup/startup_<device>.s`, with `-x assembler-with-cpp`
   - keep temporary build artifacts inside the CubeMX project or another explicitly named build output directory, not inside generated source folders
4. Run a link check when practical:
   - link all temporary object files with the CubeMX-generated linker script, using an explicit path such as `-T./STM32F407VETX_FLASH.ld`
   - pass linker options through GCC with quoted `-Wl,...` arguments when using PowerShell, for example `'-Wl,--gc-sections'` and `'-Wl,-Map=build_verify/<project>.map'`
   - generate an ELF under the verification output directory and run `arm-none-eabi-size` on it
5. Interpret results:
   - syntax-only success means the implementation is parseable but not necessarily linkable
   - full compile success means C and startup sources compile to objects, but symbol/linker issues may remain
   - link success means the project is at least compileable and linkable with the available ARM GCC toolchain and linker script
   - warnings from vendor HAL/CMSIS files should be named separately from warnings introduced by implementation code
   - include-path or type errors in `app` often indicate business-layer dependency on concrete drivers or hardware headers; correct the architecture rather than hiding the issue with broader includes
   - include-path or type errors in capability interface files often indicate leaked HAL/CubeMX/concrete-driver dependency; move those details into concrete drivers or board binding
   - if STM32CubeIDE headless build is unavailable but ARM GCC manual compile/link succeeds, report it as a manual GCC verification rather than a CubeIDE managed-build result
   - if `arm-none-eabi-gcc` or the linker script is unavailable, say so explicitly and report the remaining build risk

If build or test execution is unavailable, say so explicitly and report the remaining risk.

### CMake/Ninja/OpenOCD Build and Flash Flow

When the project contains `CMakePresets.json` or a `cmake/gcc-arm-none-eabi.cmake` toolchain file, prefer the CMake flow in `references/cmake-build-and-openocd-flash.md` over CubeIDE managed-build assumptions.

Use that reference for:

- locating local `cmake`, `ninja`, `arm-none-eabi-gcc`, and `openocd`
- asking the user to manually specify tool paths when `cmake`, `ninja`, `arm-none-eabi-gcc`, or `openocd` cannot be found from the current command environment
- configuring with the right preset
- building the `.elf`
- flashing through ST-Link/OpenOCD
- choosing software reset versus hardware reset and troubleshooting SWD connection failures

## Output Rules

Summarize:

- new or changed capability interface files, concrete driver files, board binding files, project configuration files, and business application files
- which abstract interfaces were exposed to `app` and which concrete drivers were bound behind them
- generated files touched and why
- which tasks were delegated to subagents
- which reference files were applied for implementation or review
- unresolved assumptions or user decisions still needed

Keep the final response implementation-focused. Do not describe the result as complete if business behavior or HMI logic is still ambiguous.
