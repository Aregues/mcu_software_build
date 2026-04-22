# CMake/Ninja/OpenOCD Build and Flash Reference

Use this reference when a CubeMX-generated STM32 project is CMake-based, especially when it contains `CMakePresets.json`, `cmake/gcc-arm-none-eabi.cmake`, `Core`, `Drivers`, a startup assembly file, and a linker script.

## Fast Path

1. Confirm the active project root contains:
   - `CMakeLists.txt`
   - `CMakePresets.json`
   - `cmake/gcc-arm-none-eabi.cmake`
   - `*.ioc`
   - `Core`
   - `Drivers`
2. Inspect `CMakePresets.json` and prefer an existing build preset such as `Debug`.
3. Ensure `cmake`, `ninja`, `arm-none-eabi-gcc`, and `openocd` are visible to the command process. If any of these tools cannot be found from the current command environment, ask the user to manually specify the absolute path or installation root. Do not do slow broad filesystem searches across large directories or drives.
4. Configure:

```powershell
$env:Path = 'C:\Software\Mingw64\bin;C:\ST\STM32CubeIDE_1.19.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.13.3.rel1.win32_1.0.0.202411081344\tools\bin;' + $env:Path
& 'C:\Software\Mingw64\bin\cmake.exe' --preset Debug
```

5. Build:

```powershell
$env:Path = 'C:\Software\Mingw64\bin;C:\ST\STM32CubeIDE_1.19.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.13.3.rel1.win32_1.0.0.202411081344\tools\bin;' + $env:Path
& 'C:\Software\Mingw64\bin\cmake.exe' --build --preset Debug
```

6. Confirm the `.elf` exists under the preset build directory, for example `build/Debug/<project>.elf`, and report linker memory usage if CMake prints it.

## Tool Location Notes

- Do not assume Codex receives the same PATH as the user's interactive PowerShell.
- If `where.exe cmake`, `where.exe ninja`, `where.exe openocd`, or `where.exe arm-none-eabi-gcc` fails inside Codex, ask the user to manually specify the resolved executable path or installation root before continuing.
- Inspect user-provided locations first. Avoid broad recursive searches unless the user explicitly asks for discovery and the search scope is narrow.
- On this machine, CMake and Ninja may live under `C:\Software\Mingw64\bin`.
- STM32CubeIDE may provide ARM GCC under a path like:

```text
C:\ST\STM32CubeIDE_1.19.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.13.3.rel1.win32_1.0.0.202411081344\tools\bin
```

- STM32CubeIDE OpenOCD executables and scripts can come from different plugin versions. Avoid mixing an `openocd.exe` from one plugin with scripts from another plugin when it causes Tcl recursion or compatibility errors.
- Prefer a self-contained OpenOCD install when available, for example:

```text
C:\Software\openocd\bin\openocd.exe
C:\Software\openocd\share\openocd\scripts
```

## Flash Command

For STM32F103 projects using ST-Link over SWD, use `target/stm32f1x.cfg` and `interface/stlink.cfg`.

Software reset mode:

```powershell
& 'C:\Software\openocd\bin\openocd.exe' `
  -s 'C:\Software\openocd\share\openocd\scripts' `
  -f interface/stlink.cfg `
  -f target/stm32f1x.cfg `
  -c 'adapter speed 100' `
  -c 'reset_config none' `
  -c 'program build/Debug/<project>.elf verify reset exit'
```

Hardware reset / connect-under-reset mode, only when NRST is connected:

```powershell
& 'C:\Software\openocd\bin\openocd.exe' `
  -s 'C:\Software\openocd\share\openocd\scripts' `
  -f interface/stlink.cfg `
  -f target/stm32f1x.cfg `
  -c 'adapter speed 100' `
  -c 'reset_config srst_only srst_nogate connect_assert_srst' `
  -c 'program build/Debug/<project>.elf verify reset exit'
```

Use software reset first when NRST is not connected or the user explicitly asks for software reset mode. Software reset still requires SWD to connect before reset can be issued.

## Successful OpenOCD Signals

Treat these lines as a successful connection/program/verify sequence:

```text
Info : STLINK ...
Info : Target voltage: ...
Info : [stm32f1x.cpu] Cortex-M3 ... processor detected
** Programming Finished **
** Verified OK **
** Resetting Target **
```

If OpenOCD reports a flash size different from the linker script region, mention it. For example, an STM32F103 target may report 128 KiB flash while a generated linker script uses 64 KiB.

## Failure Patterns and Fixes

`Infinite eval recursion` around `swj_newdap` / `hla newtap`:

- Usually caused by mixing an OpenOCD binary and scripts from incompatible STM32CubeIDE plugin versions.
- Use a self-contained OpenOCD install or pair the binary with matching scripts.

`STLINK ... Target voltage ...` followed by `unable to connect to the target`:

- ST-Link is detected and target power is present, but SWD cannot initialize the MCU.
- Check `SWDIO` to PA13, `SWCLK` to PA14, common `GND`, and stable target power.
- Lower SWD speed with `adapter speed 100`.
- If using manual reset, do not hold RESET for the whole command. Press RESET before starting, then release after OpenOCD starts so SWD can attach as the chip leaves reset.
- If the current firmware disabled or remapped SWD pins, use BOOT0 or connect-under-reset with NRST wired.

`clock speed 1000 kHz` after setting `adapter speed 100`:

- Some target scripts override the adapter speed while loading.
- Place `-c 'adapter speed 100'` after `-f target/...cfg` so it takes effect.

## Reporting

When reporting the result, include:

- the CMake preset used
- the build output directory and `.elf` path
- memory usage printed by the linker when available
- OpenOCD script root and interface/target cfg files
- reset mode used
- whether verification succeeded
- if flashing failed, whether ST-Link and target voltage were detected before failure
