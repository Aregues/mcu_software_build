# Peripheral Callback Rules

Read this file when using interrupts, HAL callbacks, DMA, polling loops, shared buffers, or ISR-to-main/task handoff.

## Timing and Interrupt Rules

- Keep ISR work minimal and deterministic.
- In interrupts, do only what is necessary to capture data, latch flags, update bounded state, clear hardware conditions, or notify deferred processing.
- Do not place business logic, HMI flow, long parsing, blocking waits, or unbounded retries in ISR context.
- Prefer deferred handling in the main loop, scheduled task, or dedicated processing function when work is not latency-critical.
- When polling is used, state the polling period and timeout behavior clearly in code structure or comments.
- When callbacks bridge interrupt context to application context, make the handoff explicit and auditable.
- Variables written in ISR or HAL callback context and read in the main loop, or written in the main loop and read in ISR or HAL callback context, must be declared `volatile`. Use `volatile` for visibility across interrupt and foreground contexts, but do not use it as a substitute for atomic access, critical sections, or clear ownership when multi-byte values, counters, or shared buffers can be updated concurrently.
- When FreeRTOS is present, make task wakeup paths, timeout behavior, and ISR-to-task signaling consistent with `references/freertos-development-rules.md`.

## DMA and HAL Callback Rules

- Use CubeMX-generated DMA handles and peripheral handles. Do not duplicate DMA or peripheral initialization outside CubeMX-owned init paths.
- Keep `HAL_*_RxHalfCpltCallback`, `HAL_*_RxCpltCallback`, `HAL_*_TxCpltCallback`, and `HAL_*_ErrorCallback` minimal.
- In DMA callbacks, do only bounded handoff work:
  - mark an event or status flag
  - record received length, transfer region, or error status
  - switch buffer state
  - notify the owning task, main loop, or deferred processing function
- Do not put business decisions, HMI flow, long parsing, blocking waits, dynamic allocation, or complex retry logic in HAL callbacks.
- DMA buffers must be static or owned by a clearly defined module or app component.
- Single-buffer, double-buffer, and circular-buffer designs must make producer and consumer ownership clear in code structure.
- Half-transfer and complete-transfer callbacks should only mark consumable buffer regions. Parsing and protocol handling should run later in `app` or the owning `Module` deferred processing path.
- Shared DMA buffers must use a clear snapshot, read/write index, region flag, or state flag so callback context and task or main-loop context do not modify the same region unsafely.
- DMA start and re-arm logic must live behind one clear owner function or owner module. Do not scatter DMA restart calls across unrelated callbacks and business functions.
- UART, SPI, and I2C Rx DMA re-arm logic must define error handling and recovery behavior. Do not retry or restart DMA forever inside an error callback.
- In FreeRTOS projects, DMA callback-to-task wakeup must follow `references/freertos-development-rules.md` and use ISR-safe APIs or HAL/CMSIS-RTOS interfaces allowed from interrupt context.
- If DMA ownership, half-transfer semantics, re-arm timing, or error recovery is unclear from the design, stop and resolve that uncertainty before treating the implementation as complete.

## Review Checklist

Check these before accepting callback, interrupt, polling, or DMA code:

- ISR and HAL callback bodies are short and bounded.
- Callback code only records status, marks buffer regions, updates bounded state, or notifies deferred processing.
- Variables shared between ISR/HAL callback context and the main loop are declared `volatile`, with additional atomicity or critical-section protection where needed.
- Long parsing, HMI flow, business policy, retries, and blocking waits are deferred.
- DMA buffer ownership is explicit.
- Callback and task/main-loop contexts cannot write the same region unsafely.
- DMA re-arm and error behavior are centralized and bounded.
- Polling loops have a clear period, timeout, and outcome.
- FreeRTOS handoff uses the correct ISR-safe API family when RTOS is present.
