# Embedded Hardware Mock Strategy

Host-side tests must not require MCU hardware, CubeMX startup, interrupts, DMA hardware, or vendor HAL side effects.

## Business Layer

Test `app` or `APP` logic through abstract interfaces, fakes, and deterministic time inputs.

- Use fakes for sensors, displays, buttons, motors, storage, communication, and clocks.
- Assert state transitions, emitted commands, error handling, and scheduling decisions.
- Do not include HAL headers in business-layer tests unless the existing architecture already exposes them and the slice is explicitly about removing that leak.

## Driver and Component Layer

Test concrete drivers against fake bus or register-access interfaces.

- Use an I2C/SPI/UART fake that records transfers and can return scripted responses.
- Assert register addresses, payloads, retry behavior, status mapping, and data conversion.
- Stub timing delays instead of sleeping.
- Keep real HAL calls behind a HAL adapter boundary.

## HAL Adapter and Board Layer

Prefer narrow compile checks and wrapper-level tests. Full behavior often requires on-target validation.

- Stub HAL functions only when the adapter has a narrow deterministic contract.
- Do not mock large HAL subsystems just to force host tests through generated code.
- For board binding, verify object construction, dependency injection, and selected addresses or pins where those are represented as data.
- Record remaining hardware validation risks for interrupts, DMA, timing, watchdog, low-power modes, and electrical behavior.

## Interrupts, DMA, and Callbacks

Model the handoff contract, not the hardware event.

- Call the callback or dispatcher function directly with fake inputs.
- Assert buffer ownership, event flags, queue pushes, and error paths.
- Keep ISR-safe shared data small and deterministic in tests.
