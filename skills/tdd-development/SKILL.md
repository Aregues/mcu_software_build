---
name: tdd-development
description: Execute test-first embedded firmware implementation from docs/releases/VERSION/software_design.md by deriving behavioral test cases, writing host-side C tests under the project-root test/ directory, implementing code slice by slice, rerunning tests until each slice passes, and reporting blockers. Use for new features, clear software design documents, complex implementation where TDD is requested or preferred, host-side unit tests for MCU business logic, and subagent-assigned independent TDD slices. Treat this skill as a sibling of cubemx-code-implementation, not a child workflow.
---

# TDD Development

Use this skill for test-first implementation on an existing MCU or CubeMX project when the main orchestrator has supplied a release directory, software design document, architecture constraints, allowed write scope, and forbidden edit areas.

This skill executes implementation slices. The main orchestrator keeps ownership of architecture, scope, final integration, and user-facing decisions.

## Required Inputs

- Active release directory, usually `docs/releases/<version>`.
- Software design document at `docs/releases/<version>/software_design.md`.
- Any confirmed requirements, ECR constraints, hardware.json, cubemx_build.md, and project notes passed by the orchestrator.
- Explicit allowed edit scope and forbidden edit areas.
- Exact slice assignment when invoked as a subagent.

If the software design document, write scope, or forbidden edit areas are missing, stop and report the missing input instead of guessing.

## Reference Files

Load these references only when needed:

- `references/tdd-slice-rules.md`: read before deriving or accepting TDD slices.
- `references/embedded-hardware-mock.md`: read before writing host-side tests around HAL, board binding, drivers, interrupts, DMA, sensors, displays, storage, or other hardware boundaries.
- `references/host-unit-test-mingw.md`: read before compiling or running host-side C tests on Windows or PowerShell.
- `references/subagent-tdd-contract.md`: read before accepting or dispatching subagent TDD slice work.

## Core Workflow

1. Read the release directory inputs, software design document, architecture constraints, allowed write scope, and forbidden edit areas.
2. Extract testable requirements from the software design document and split them into behavior-based TDD slices.
3. For each slice, identify the target layer, existing module, public API, internal helper boundary, expected test file, expected implementation files, hardware boundary, and done condition.
4. Create or update tests first under the project-root `test/` directory. Do not create `tests/`.
5. Run host-side tests. If a new test does not fail because of the not-yet-implemented target behavior, correct the test, mock, fake, or boundary before implementation.
6. Implement the minimum production code needed for the current slice while preserving the existing architecture and file organization.
7. Run tests again. If they fail, return to implementation until the current slice passes or a clear blocker is reached.
8. Continue with the next slice until the orchestrator-assigned scope is complete.
9. Report completed slices, test results, changed paths, incomplete slices, toolchain gaps, and hardware-verification risks.

## Architecture Rules

Follow the main orchestrator, software design document, generated CubeMX skeleton, and local project conventions. Do not invent a new folder layout.

Use the existing `Common`, `Module`, `Board`, `app` or `APP`, and `Config` layering when present or required by the project:

- `test/` owns host-side unit tests, mocks, fakes, and test-only fixtures.
- `Common` owns platform-neutral interfaces and utilities.
- `Module` owns reusable drivers, HAL adapters, device protocols, and components.
- `Board` owns concrete binding to CubeMX handles, pins, buses, addresses, timers, and board resources.
- `app` or `APP` owns business logic, state machines, scheduling policy, HMI flow, and orchestration.
- `Config` owns tunable parameters.

Do not move, delete, or reorganize CubeMX-generated directories. If generated files must be edited, use stable user-code sections when possible.

## Test Placement

All new or updated host-side tests must live under the project-root `test/` directory.

Prefer project-local test conventions when they already exist. If none exist, create small C tests that can be compiled by MinGW on the host. Keep hardware effects behind mocks, fakes, or stubs so tests can run without MCU hardware.

Use `scripts/run_host_unit_tests.ps1` from the project root when no stronger project-specific test runner exists. This runner searches for MinGW `gcc.exe` and fails clearly if the host toolchain is unavailable.

## Subagent Use

The main orchestrator may assign this skill to a subagent for independent slices. Read `references/subagent-tdd-contract.md` before doing so.

Process slices serially when they modify the same core file, public API, shared state machine, scheduler, startup path, callback dispatch, or global state.

Stop and report to the main orchestrator when a slice requires:

- changing the file organization or CubeMX layout
- modifying forbidden files
- resolving conflicting requirements or design decisions
- choosing a hardware behavior that is not mockable from the design
- expanding public APIs beyond the assigned scope
- changing shared state machines in a way that affects another active slice

## Output Rules

Final reports must include:

- completed slices and their requirement mapping
- tests added or changed under `test/`
- implementation paths changed
- exact test commands and results
- incomplete slices and why they stopped
- missing MinGW or other toolchain blockers
- remaining hardware or on-target verification risks
