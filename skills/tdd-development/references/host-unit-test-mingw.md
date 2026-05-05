# Host Unit Test Flow on Windows

Use PowerShell syntax by default.

When the project has an existing host test runner, use it first. Otherwise use:

```powershell
.\skills\tdd-development\scripts\run_host_unit_tests.ps1
```

If local PowerShell execution policy blocks direct script execution, run the same script with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\skills\tdd-development\scripts\run_host_unit_tests.ps1
```

The runner:

- searches for MinGW `gcc.exe` through `find_mingw.ps1`
- scans the project-root `test/` directory
- compiles C test entries with `-DHOST_UNIT_TEST=1`
- runs each generated test executable
- returns non-zero for missing toolchain, missing tests, compile failure, or runtime failure

MinGW lookup order:

1. directories from `PATH`
2. `C:\msys64\mingw64\bin`
3. `C:\msys64\ucrt64\bin`
4. `C:\msys64\mingw32\bin`
5. `C:\MinGW\bin`

If MinGW is unavailable, report the missing toolchain as a blocker. Do not mark tests as passed.

Default test discovery treats these files as standalone test entries:

- `test/test_*.c`
- `test/*_test.c`
- `test/*.test.c`
- any `test/*.c` file containing `int main(`

Non-entry C files under `test/` are compiled as support sources. Extra production sources or include paths can be passed to the runner when needed.
