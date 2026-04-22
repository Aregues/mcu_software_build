---
name: embedded-gdb-openocd-debug
description: Enable Codex to debug STM32 and ARM Cortex-M firmware with OpenOCD and arm-none-eabi-gdb. Use when Codex needs to operate an OpenOCD GDB server, connect arm-none-eabi-gdb to a target, set breakpoints such as main, step through firmware, inspect C variables, registers, stack frames, memory, peripheral registers, or diagnose ST-Link/SWD/OpenOCD connection and reset-mode problems.
---

# Embedded GDB OpenOCD Debug

Use this skill to run or direct an interactive or scripted debug session for STM32 firmware using OpenOCD plus `arm-none-eabi-gdb`.

## Reference Files

Load `references/openocd-gdb-debugging.md` when the debug task involves:

- starting OpenOCD as a GDB server
- connecting `arm-none-eabi-gdb`
- setting, listing, disabling, or deleting breakpoints
- stepping, continuing, halting, resetting, or restarting the target
- reading variables, registers, stack frames, memory, peripheral registers, or backtraces
- resolving `unable to connect to the target`, reset-mode, SWD speed, or OpenOCD script compatibility issues

## Workflow

1. Identify the firmware ELF, OpenOCD executable, OpenOCD scripts root, target cfg, interface cfg, and `arm-none-eabi-gdb` executable.
2. If any required tool path cannot be resolved from the current command environment, ask the user to manually specify the executable path or installation root. Do not run slow broad recursive searches across large directories or drives.
3. Start OpenOCD with the target-specific interface and target scripts, low SWD speed when needed, and the reset mode appropriate for the hardware wiring.
4. Connect GDB to OpenOCD on port `3333`.
5. Load symbols from the ELF, halt or reset-halt the target, set the requested breakpoints, and continue to the breakpoint.
6. Use GDB commands to inspect the requested program state.
7. When scripting a one-shot debug check, shut down OpenOCD at the end with `monitor shutdown` or stop the spawned process.

## Reset Mode Guidance

- Prefer software reset (`reset_config none`) when NRST is not wired or the requested debug mode is software reset.
- Use connect-under-reset (`reset_config srst_only srst_nogate connect_assert_srst`) only when NRST is wired from the debug probe to the target board.
- If manual RESET coordination is required, instruct the operator not to hold RESET for the whole command. They should press RESET before OpenOCD starts and release shortly after OpenOCD begins connecting so SWD can attach as the chip leaves reset.

## Reporting

Report:

- whether OpenOCD detected ST-Link and target voltage
- whether it detected the CPU core
- whether GDB connected successfully
- breakpoints set and where execution stopped
- variable, register, memory, or stack values inspected during the debug task
- any remaining hardware or reset-mode assumptions
