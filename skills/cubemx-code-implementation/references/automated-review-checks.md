# Automated Review Checks

Read this file when reviewing completed implementation work, subagent output, or suspected embedded style violations.

These checks are a first pass before manual review. A hit is not automatically a failure, but every hit must be explained as one of:

- acceptable with reason
- needs manual review
- violation requiring rewrite

If a hit confirms a violation, require rewrite before integrating the code.

## Scope

Run checks first on implementation-owned paths:

- `app`
- `Module`

Treat these as logical layers inside those paths:

- core interface files, usually `Module/<name>/<name>.h` and `Module/<name>/<name>.c`
- concrete driver files, such as `Module/<name>/<name>_gpio.*`, `Module/<name>/<name>_pwm.*`, or `Module/<name>/<name>_i2c.*`
- board binding files under a dedicated top-level directory such as `Board` or `board`
- business application files under `app`

When integration code was changed, also include CubeMX user-code integration points:

- `Core/Src`
- `Core/Inc`

Prefer `rg` for text checks. On Windows, use PowerShell snippets only where line counting or structure-aware review is needed.

## Dynamic Memory

Dynamic allocation is forbidden unless the software design document explicitly allows it and gives bounded behavior.

Use:

```powershell
rg -n "\b(malloc|calloc|realloc|free)\s*\(" app Module Core/Src Core/Inc
```

Default judgment:

- hit in project implementation code: violation requiring rewrite
- hit in vendor or generated driver code outside the review scope: ignore unless the implementation newly introduced it
- allowed only when the software design document explicitly permits dynamic allocation and states limits, ownership, and failure handling

## Suspicious Infinite Loops

Check for infinite loops that may lack timeout, blocking wait, task yield, or safe exit.

Use:

```powershell
rg -n "while\s*\(\s*(1|true)\s*\)|for\s*\(\s*;\s*;\s*\)" app Module Core/Src Core/Inc
```

Default judgment:

- not automatically a failure
- requires manual review
- violation if the loop lacks timeout, bounded exit, event wait, `osDelay`, task yield, blocking queue/notification wait, or documented safe-state behavior

## Module-to-App Dependency Violation

Core interface files and concrete drivers must not depend on `app` business headers. Board binding is the preferred place to map app-level configuration into concrete init arguments.

Use:

```powershell
rg -n "#\s*include\s*[<\"].*app[/\\]" Module
```

Default judgment:

- hit is a violation requiring rewrite
- if the only include is a deliberately narrow top-level project configuration header such as `Config/project_config.h`, review the design: prefer injecting configuration through board binding, a config struct, init argument, or explicit macro mapping; do not allow broad app-layer dependency

## Business-Layer Hardware Dependency Violation

Business application code must depend on abstract interfaces, not HAL, CubeMX hardware headers, generated peripheral headers, or concrete driver headers.

Use:

```powershell
rg -n "#\s*include\s*[<\"].*(stm32.*hal|main\.h|gpio\.h|tim\.h|i2c\.h|spi\.h|usart\.h|adc\.h|dma\.h|_gpio\.h|_pwm\.h|_i2c\.h|_spi\.h|_uart\.h)" app
```

Default judgment:

- hit in dedicated board binding files such as `Board/board.c` may be acceptable because board binding owns concrete hardware-resource injection
- hit in business logic files is a violation requiring rewrite
- hit in `app/board.*` or `app/*board*.*` usually indicates board binding was mixed into the business layer; move it to a dedicated `Board` or `board` directory unless the existing project has an explicit, documented exception

## Core Interface Hardware Pollution

Core interface headers must stay platform-neutral and must not expose HAL, CubeMX, register, board, or concrete-driver details.

Use:

```powershell
rg -n "#\s*include\s*[<\"].*(stm32.*hal|main\.h|gpio\.h|tim\.h|i2c\.h|spi\.h|usart\.h|adc\.h|dma\.h|_gpio\.h|_pwm\.h|_i2c\.h|_spi\.h|_uart\.h)" Module
rg -n "\b(GPIO_TypeDef|GPIO_PinState|I2C_HandleTypeDef|SPI_HandleTypeDef|UART_HandleTypeDef|TIM_HandleTypeDef|DMA_HandleTypeDef|ADC_HandleTypeDef)\b" Module
```

Default judgment:

- hit in concrete driver files such as `*_gpio.h`, `*_pwm.h`, or `*_i2c.h` can be acceptable
- hit in a core interface file such as `xxx.h` or `xxx.c` is a violation requiring rewrite
- if file naming does not clearly separate core and concrete files, manually classify the file before judging

## Abstract-to-Concrete Cast Review

Business code must not cast abstract base pointers to concrete derived types. Concrete drivers may cast from base to derived inside their own ops functions.

Use:

```powershell
rg -n "\([A-Za-z0-9_]+_(gpio|pwm|i2c|spi|uart|adc)_t\s*\*\)" app Module
```

Default judgment:

- hit in concrete driver implementation is usually acceptable when it is inside an ops function
- hit in `app` business logic is a violation requiring rewrite
- hit in board binding needs manual review; board binding should usually keep concrete objects private and pass abstract pointers upward

## Board Binding Location Review

Board binding must live in a dedicated top-level directory such as `Board` or `board`, alongside `app` and `Module`.

Use:

```powershell
rg -n "(board_init|board_get_|static\s+.*_(gpio|pwm|i2c|spi|uart|adc)|HAL_.*HandleTypeDef|GPIO_TypeDef|GPIO_PinState)" app Module
```

Default judgment:

- hit in `app` needs manual review and is usually a violation when it creates concrete objects, injects CubeMX resources, or includes concrete driver/HAL types
- hit in `Module` needs manual review and is usually a violation when it binds project board resources rather than implementing a reusable concrete driver
- acceptable alternatives are dedicated top-level board binding files such as `Board/board.c`, `Board/board.h`, `board/board.c`, or a project-specific top-level BSP binding directory

## Scattered Project Parameters

Look for tunable parameter names and local config headers that may indicate parameters are not centralized in a top-level project configuration header such as `Config/project_config.h`.

Limit this check to implementation-owned paths by default. Do not include `Core/Src` or `Core/Inc` for this check unless user code in those folders clearly owns project parameters; generated CubeMX, HAL, CMSIS, and FreeRTOS code commonly use words such as stack, queue, period, and delay.

Use:

```powershell
rg -n "^\s*(#\s*define|static\s+const|const\s+|enum\b).*\b(timeout|threshold|retry|calib|calibration|stack|queue|period|interval|delay)\b" app Module
rg -n "(_config\.h|config\.h)" app Board board Module
```

Default judgment:

- not automatically a failure
- requires checking whether project-tunable values are centralized in a top-level project configuration header such as `Config/project_config.h`
- violation if timeout, threshold, retry, calibration, task-period, queue-depth, or stack-size values are hard-coded in module implementation files without traceable project configuration
- violation if a module creates an informal project-level `*_config.h` hub without an explicit design exception
- violation if board-resource binding or project-wide configuration mapping is placed in `app` business code instead of `Board` or a top-level configuration layer

## Suspicious RTOS Delay Usage

`osDelay` is appropriate for periodic pacing, not as a substitute for event synchronization.

Use:

```powershell
rg -n "\bosDelay\s*\(" app Module Core/Src Core/Inc
```

Default judgment:

- acceptable for periodic tasks when the period is documented or clearly named
- needs manual review when used near communication waiting, data readiness, retries, or shared resource sequencing
- violation if it is being used where a queue, semaphore, direct task notification, or event flag is the correct synchronization primitive

## ISR and Callback Length

ISR functions and HAL callbacks should stay minimal and deterministic. Flag ISR or callback bodies longer than 40 lines for manual review.

Use this PowerShell review helper from the CubeMX project root:

```powershell
$paths = @('app','Module','Core/Src','Core/Inc') | Where-Object { Test-Path $_ }
$pattern = '^\s*(void|static\s+void)\s+([A-Za-z0-9_]*(IRQHandler|Callback))\s*\('
Get-ChildItem -Path $paths -Recurse -Include *.c,*.h |
  ForEach-Object {
    $file = $_.FullName
    $lines = Get-Content -LiteralPath $file
    for ($i = 0; $i -lt $lines.Count; $i++) {
      if ($lines[$i] -match $pattern) {
        $depth = 0
        $start = $i
        $seenBody = $false
        for ($j = $i; $j -lt $lines.Count; $j++) {
          $depth += ([regex]::Matches($lines[$j], '\{')).Count
          if ($depth -gt 0) { $seenBody = $true }
          $depth -= ([regex]::Matches($lines[$j], '\}')).Count
          if ($seenBody -and $depth -eq 0) {
            $length = $j - $start + 1
            if ($length -gt 40) { "$file:$($start + 1): ISR/callback body is $length lines" }
            break
          }
        }
      }
    }
  }
```

Default judgment:

- not automatically a failure
- requires manual review when over 40 lines
- violation if the function contains business logic, HMI flow, long parsing, blocking waits, retry loops, dynamic allocation, or substantial cross-module orchestration

## DMA and HAL Callback Review

HAL callback presence is normal in CubeMX projects, so these hits are review triggers, not automatic failures.

Use:

```powershell
rg -n "HAL_.*(RxHalfCplt|RxCplt|TxCplt|Error)Callback" app Module Core/Src Core/Inc
rg -n "\b(HAL_Delay|osDelay|malloc|calloc|realloc|free)\s*\(" app Module Core/Src Core/Inc
```

Default judgment:

- not automatically a failure
- requires manual review for each DMA or HAL callback hit
- violation if a callback contains business logic, HMI flow, long parsing, blocking waits, dynamic allocation, complex retry logic, or scattered DMA restart logic
- violation if DMA buffer ownership is unclear or callback and main-loop/task context can modify the same buffer region without a clear handoff flag, index, or snapshot
- violation if `HAL_*_ErrorCallback` restarts DMA indefinitely without bounded recovery behavior
- acceptable when the callback only records status, marks buffer region availability, updates bounded state, or notifies deferred processing

## Watchdog Review

IWDG or WWDG presence is normal when the design or CubeMX configuration requires a watchdog, so these hits are review triggers, not automatic failures.

Use:

```powershell
rg -n "\b(HAL_IWDG_Refresh|HAL_WWDG_Refresh|IWDG|WWDG)\b" app Module Core/Src Core/Inc
```

Default judgment:

- not automatically a failure
- acceptable when refresh is centralized in the documented app-level health monitor or system supervisor
- violation if `Module` drivers refresh the watchdog directly without an explicit design exception
- violation if watchdog refresh appears in ISR or DMA callback context without explicit design justification
- violation if multiple unrelated code paths refresh the watchdog independently
- violation if refresh timing, timeout, health-report deadline, or startup self-check timeout appears as unexplained magic numbers instead of project configuration
- violation if a required hardware watchdog is absent from the CubeMX framework and the implementation substitutes an ad hoc software timer without classifying the framework gap
- requires manual review when reset-cause handling exists, to confirm that low-level drivers do not make business decisions and that app or diagnostics own policy

## Review Output Format

For each reviewed implementation result, report:

- automated checks run
- hits found
- judgment for each hit
- rewrite required or not
- remaining manual-review concerns

Do not integrate subagent code until confirmed violations are rewritten.
