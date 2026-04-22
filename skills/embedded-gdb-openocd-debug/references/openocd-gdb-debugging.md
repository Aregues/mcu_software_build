# OpenOCD and arm-none-eabi-gdb Debugging

This reference covers practical OpenOCD + `arm-none-eabi-gdb` debugging for STM32/ARM Cortex-M firmware.

## Tool Path Rules

- Do not assume Codex sees the same PATH as the user's interactive PowerShell.
- If `openocd`, `arm-none-eabi-gdb`, or the ELF path cannot be found from the current command environment, ask the user to manually specify the absolute executable path, installation root, or ELF path before continuing.
- Inspect operator-provided paths first. Avoid slow broad recursive searches unless manual discovery is explicitly requested and the search scope is narrow.
- Keep environment changes local to the current command unless the user explicitly asks to modify system PATH.

## Start OpenOCD

Example for STM32F103 with ST-Link and a self-contained OpenOCD install:

```powershell
& 'C:\Software\openocd\bin\openocd.exe' `
  -s 'C:\Software\openocd\share\openocd\scripts' `
  -f interface/stlink.cfg `
  -f target/stm32f1x.cfg `
  -c 'adapter speed 100' `
  -c 'reset_config none'
```

Use `reset_config none` for software reset mode when NRST is not wired.

Use connect-under-reset only when NRST is wired:

```powershell
& 'C:\Software\openocd\bin\openocd.exe' `
  -s 'C:\Software\openocd\share\openocd\scripts' `
  -f interface/stlink.cfg `
  -f target/stm32f1x.cfg `
  -c 'adapter speed 100' `
  -c 'reset_config srst_only srst_nogate connect_assert_srst'
```

Successful OpenOCD startup normally includes:

```text
Info : STLINK ...
Info : Target voltage: ...
Info : [stm32f1x.cpu] Cortex-M3 ... processor detected
Info : starting gdb server ... on 3333
```

## Connect GDB

Interactive session:

```gdb
file build/Debug/<project>.elf
target remote localhost:3333
monitor reset halt
break main
continue
```

One-shot PowerShell batch example:

```powershell
& '...\arm-none-eabi-gdb.exe' 'build\Debug\<project>.elf' `
  -batch `
  -ex 'set pagination off' `
  -ex 'target remote localhost:3333' `
  -ex 'monitor reset halt' `
  -ex 'break main' `
  -ex 'continue' `
  -ex 'info breakpoints' `
  -ex 'frame' `
  -ex 'monitor shutdown'
```

OpenOCD may prefer:

```gdb
target extended-remote localhost:3333
```

Use it when OpenOCD warns that `target extended-remote` is preferred.

## Breakpoints

Set a breakpoint:

```gdb
break main
break main.c:74
break HAL_Init
```

List breakpoints:

```gdb
info breakpoints
```

Disable, enable, or delete:

```gdb
disable 1
enable 1
delete 1
delete
```

Cortex-M flash breakpoints are hardware breakpoints. OpenOCD/GDB may print:

```text
Note: automatically using hardware breakpoints for read-only addresses.
```

This is expected.

## Run Control

Continue to the next breakpoint:

```gdb
continue
```

Step over the current source line:

```gdb
next
```

Step into the current function call:

```gdb
step
```

Step one assembly instruction:

```gdb
stepi
nexti
```

Run until the current function returns:

```gdb
finish
```

Halt or reset through OpenOCD:

```gdb
monitor halt
monitor reset halt
monitor reset init
```

## Locate Current Stop Position

Use these commands to determine where execution is currently stopped, where firmware appears stuck, or what code is currently running.

Show the current source location and frame:

```gdb
frame
```

Show the call stack:

```gdb
backtrace
bt
```

Show source lines around the current program counter:

```gdb
list
list *$pc
```

Print the current program counter and link register:

```gdb
p/x $pc
p/x $lr
```

Map the current program counter to a source line when debug symbols are available:

```gdb
info line *$pc
```

Disassemble the current instruction when source mapping is unavailable or the target is in startup/ISR code:

```gdb
x/i $pc
x/8i $pc
```

## Inspect Variables

Print a C variable:

```gdb
print variable_name
p variable_name
```

Print as hex:

```gdb
p/x variable_name
```

Print a structure field:

```gdb
p hgpio.Init.Pin
```

Print a pointer target:

```gdb
p *ptr
```

Display a value every time execution stops:

```gdb
display variable_name
display/x variable_name
```

If GDB reports `<optimized out>`, switch to a debug build such as `-O0 -g3` or stop in a scope where the local variable is still live.

## Inspect Registers

All common registers:

```gdb
info registers
i r
```

Specific registers:

```gdb
info registers pc
info registers sp
info registers lr
info registers xpsr
```

Print register values directly:

```gdb
p/x $r0
p/x $r1
p/x $sp
p/x $lr
p/x $pc
p/x $xpsr
```

All exposed registers:

```gdb
info all-registers
```

## Inspect Stack and Frames

Show current frame:

```gdb
frame
```

Show call stack:

```gdb
backtrace
bt
```

Show local variables in the current frame:

```gdb
info locals
```

Show function arguments:

```gdb
info args
```

Select a caller frame:

```gdb
up
down
frame 1
```

## Inspect Memory and Peripheral Registers

Read a 32-bit word as hex:

```gdb
x/wx 0x4001100C
```

Read multiple words:

```gdb
x/16wx 0x20000000
```

Read bytes:

```gdb
x/32xb 0x08000000
```

Read an expression address:

```gdb
x/wx &variable_name
```

For STM32 peripheral registers, use the reference manual base address plus register offset. Example for a GPIO ODR register:

```gdb
x/wx 0x4001100C
```

## Troubleshooting

`unable to connect to the target` after ST-Link and target voltage are detected:

- Check SWDIO, SWCLK, GND, and target power.
- Lower speed with `adapter speed 100`, placing the command after target cfg if a script overrides the speed.
- Use software reset only if SWD can connect without NRST.
- Use connect-under-reset only if NRST is wired.
- When coordinating manual RESET, release it shortly after OpenOCD starts; do not hold it until the command exits.
- Try BOOT0 when the flashed application may disable or conflict with SWD pins.

`Infinite eval recursion` involving `swj_newdap` or `hla newtap`:

- Do not mix OpenOCD binaries and script directories from incompatible STM32CubeIDE plugin versions.
- Prefer a self-contained OpenOCD install where `bin/openocd.exe` and `share/openocd/scripts` come from the same package.

GDB connects but cannot print source variables:

- Confirm the ELF loaded by GDB is the same firmware on the target.
- Use a Debug build with symbols, for example `-g3`.
- Avoid optimized builds when inspecting local variables.

Port `3333` already in use:

- Check for a stale OpenOCD process and stop it if it belongs to the previous debug session.
- Or start OpenOCD with a different GDB port using OpenOCD configuration commands.
