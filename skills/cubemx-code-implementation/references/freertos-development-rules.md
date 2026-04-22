# FreeRTOS Development Rules

Read this file only when the generated CubeMX project includes FreeRTOS middleware or RTOS-generated source files.

## Scope

Use these rules to constrain:

- task creation and ownership
- task priority selection
- stack size estimation
- queue, semaphore, mutex, and notification choice
- ISR-to-task handoff
- delay, timeout, and polling behavior

These rules are an extension of the main skill's embedded style: determinism, bounded resource use, analyzable timing, and controlled fault behavior.

## Task Model

- Create tasks only for responsibilities that need concurrency separation.
- Do not create a separate task for every module by default.
- Prefer one task to own one coherent runtime responsibility, for example:
  - control loop
  - communication service
  - sensor acquisition and preprocessing
  - HMI update
- Keep driver code in `Module`; keep task orchestration and scheduling ownership in `app`.
- If a task exists only to poll one flag and call one function, reconsider whether it should instead be a periodic service inside an existing task.

## Priority Rules

- Assign priority from response-time need and blocking sensitivity.
- A safety or control task may be higher priority than telemetry or HMI.
- Do not raise priority to mask poor locking or blocking design.
- Prefer a small number of distinct priority levels with clear meaning.
- Document why each nontrivial task priority is higher, lower, or equal to the others.
- If two tasks share a resource often, review whether the priority relationship creates avoidable contention or inversion risk.

## Stack Rules

- Estimate stack size from:
  - deepest expected call chain
  - local variable and buffer size
  - library calls
  - printf-style formatting use
  - worst-case error path
- Avoid oversized stacks without reason; they hide poor memory discipline.
- Avoid undersized stacks justified only by "seems enough".
- If exact evidence is unavailable, use a conservative estimate and mark the stack assumption for later verification.
- Prefer moving large transient buffers out of task stacks when a shared static buffer or owned module buffer is safer and clearer.

## Synchronization Selection

Choose synchronization primitives by ownership and data shape:

- direct task notification:
  use for one-to-one event signaling with minimal overhead
- queue:
  use for ordered message or sample transfer with bounded depth
- binary semaphore:
  use for simple event release when notification is not suitable
- counting semaphore:
  use only when accumulated event counts are meaningful
- mutex:
  use for shared resource protection with ownership semantics
- recursive mutex:
  avoid unless existing structure makes it unavoidable and the reasoning is explicit
- event flags or event groups:
  use for small sets of independent readiness or state bits

Do not use a queue when only a single wakeup bit is needed. Do not use a mutex as a generic event signal.

## Delay, Timeout, and Polling Rules

- Use `osDelay` or equivalent periodic delay only for genuinely periodic work.
- Do not use `osDelay` to wait for another task, ISR, or device event that should be signaled explicitly.
- Prefer bounded blocking waits with explicit timeout values for communication and resource acquisition.
- Timeouts must have a documented outcome:
  - retry
  - degrade
  - fault report
  - safe-state transition
- Avoid tight polling loops in tasks. If polling is necessary, define the polling period and the reason it is acceptable.

## ISR and RTOS Handoff

- Keep ISR work minimal.
- In ISR context, capture data, clear hardware conditions, and notify the owning task.
- Use the RTOS-safe interrupt APIs required by the project's wrapper layer.
- Do not call task-context-only APIs from ISR context.
- After ISR-to-task handoff, keep ownership clear about who consumes the data and who resets the signal.

## Shared Resource Rules

- Protect shared buses, shared communication peripherals, and shared storage with a clear owner or a narrow mutex scope.
- Avoid nested locks where possible.
- Do not hold a mutex across long waits, peripheral completion polling, or unrelated processing.
- If one task should be the sole owner of a peripheral, prefer message passing to that owner task instead of cross-task direct access.

## Review Checklist

Check these before accepting RTOS-based code:

- task count is justified
- task priorities are reasoned, not arbitrary
- stack sizes are explained or conservatively justified
- queues and semaphores are bounded
- mutex use is narrow and ownership is clear
- `osDelay` is used only for periodic pacing, not as a hidden synchronization tool
- ISR-to-task handoff uses the correct API family
- task blocking and timeout behavior matches the software design document
- no task contains unbounded polling, retry, or blocking behavior without explicit justification
