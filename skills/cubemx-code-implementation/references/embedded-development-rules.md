# Embedded Development Rules

Read this file before writing or reviewing implementation code in core interface files, concrete drivers, board binding files, business application code, or CubeMX user-code blocks.

## Development Style

Use deterministic, bounded, and reviewable embedded code.

- Prefer simple control flow over clever abstraction.
- Make worst-case behavior understandable from source.
- Keep runtime behavior bounded: loops, retries, buffers, waits, and queues must have clear limits.
- Prefer static allocation and bounded buffers unless the software design explicitly justifies another approach.
- Do not introduce dynamic memory unless the software design document explicitly requires it and defines bounds, ownership, and failure handling.
- Avoid hidden allocation, hidden background work, and hidden ownership transfer.
- Do not treat average-case timing as sufficient when the design cares about real-time response.
- Match naming, HAL usage, and file organization to the existing project style.
- Add comments only for timing assumptions, state ownership, protocol rules, safety constraints, or non-obvious behavior.

## Layering Rules

- Split module code into core interface, concrete driver, board binding, and business application layers.
- Keep core interface files focused on stable abstraction: base struct, ops table, status values, capability flags, and public wrapper functions.
- Keep concrete drivers focused on device-level behavior: init, read, write, parse, command, status, and fault detection.
- Keep board binding focused on object creation, CubeMX resource injection, concrete-driver initialization, and exposing abstract base pointers to application code.
- Keep board binding in a dedicated top-level directory such as `Board` or `board`, at the same level as `app` and `Module`.
- Do not put board binding files inside concrete driver folders, and do not mix them into the business `app` directory.
- Keep `app` code focused on use-case logic: state machine, control flow, policy, HMI, inter-module coordination, scheduling, and system health.
- Core interface headers must not depend on HAL, CubeMX-generated headers, board headers, register headers, GPIO/PWM/I2C/SPI/UART/DMA/timer types, or concrete driver headers.
- Concrete drivers may depend on core interface headers, HAL/CubeMX, BSP-style glue, and local utility headers.
- Board binding may depend on concrete driver headers, CubeMX handles, generated pin names, and hardware-resource declarations.
- `app` may depend only on core interface headers and project-level abstract services.
- `app` must not include HAL headers, register headers, generated hardware headers, or concrete driver headers.
- Concrete drivers and core interfaces must not depend on `app` business logic.
- Do not let business rules leak into device drivers.
- Do not let device register details leak upward into `app` unless the software design explicitly calls for that exposure.
- If a shared contract is needed between `app` and a device, define a narrow abstract interface and keep ownership clear.
- Use capability queries or extension interfaces for optional device behavior rather than forcing application code to cast to a concrete type.

## File and Interface Style

- Prefer one module, one responsibility, one public header.
- Public headers should expose only the types, constants, and APIs needed by other layers.
- Keep private helpers in the `.c` file unless they are intentionally shared.
- Use explicit prefixes tied to the module name for public symbols.
- For polymorphic modules, put the base struct as the first member of every derived struct and bind behavior through a `static const xxx_ops_t` function table during initialization.
- Keep public wrapper functions responsible for null checks and unsupported-operation handling.
- Do not expose concrete derived types through application-facing headers when an abstract base pointer is sufficient.
- Prefer fixed-width integer types for on-wire data, registers, counters, and persistent data.
- Document units for externally visible values such as `ms`, `us`, `mV`, `deg`, or raw ADC counts.
- For APIs that can fail, return explicit status values or error codes instead of relying on comments or implicit conventions.
- Avoid scattered writable globals. If global state is necessary, centralize it behind one owner module.

## State, Concurrency, and Data Rules

- Make shared data ownership explicit.
- When data is touched from both interrupt and non-interrupt context, use the smallest correct synchronization method and keep the protected region short.
- Use `volatile` only for data whose access semantics require it; do not use it as a substitute for synchronization design.
- Prefer snapshot copies, double-buffer handoff, or flag-and-process patterns when they simplify reasoning.
- Keep state machines explicit: named states, named events, clear transition conditions, and clear safe-state behavior.

## Error Handling and Fault Style

- Match the software design document's fault strategy and degraded-mode intent.
- Detect faults close to where they occur, but decide business impact in the owning layer.
- Distinguish initialization failure, runtime communication failure, invalid data, timeout, and safety-triggered shutdown.
- Do not swallow hardware or protocol errors silently.
- For recoverable faults, define bounded retry or recovery behavior.
- For non-recoverable or safety-relevant faults, drive the system toward the documented safe state and expose status upward.
- If the required recovery policy is unclear from the design, stop and ask the user instead of inventing one.

## Traceability Rules

- Keep important behavior traceable to the requirement or software design when the link is not obvious from naming alone.
- When a parameter, timeout, threshold, or retry count comes from a document, keep the code name and surrounding comment aligned with that meaning.
- If a value is temporarily inferred because the source document is incomplete, mark it clearly as `TBD` or assumption-oriented rather than presenting it as final fact.

## Forbidden Patterns

- Do not rewrite CubeMX-generated initialization outside intended user extension points unless there is no viable alternative.
- Do not duplicate peripheral initialization already owned by CubeMX.
- Do not block indefinitely waiting for hardware response.
- Do not use unbounded queues, unbounded recursion, or uncontrolled retry loops.
- Do not put application policy into ISR context.
- Do not let core interface or concrete driver code call into `app` business logic.
- Do not let `app` include concrete driver headers or cast abstract base pointers to derived concrete types.
- Do not put HAL, GPIO, PWM, I2C, SPI, UART, DMA, timer, or register details in core interface headers.
- Do not expand the base interface for one concrete device's special feature; use capability queries or an explicit extension interface.
- Do not mix HMI flow and low-level register or protocol operations in the same function.
- Do not bypass the software design document's layering, timing, or fault assumptions without calling out the mismatch.
