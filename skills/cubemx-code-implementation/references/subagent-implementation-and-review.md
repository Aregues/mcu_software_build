# Subagent Implementation and Review

Use this reference when dispatching implementation or review subagents for independent module-driver work in a CubeMX-based project.

## Implementation Subagent Tasks

Every module-driver subagent task must state that the subagent is not alone in the codebase, must not revert others' changes, and must keep edits inside its owned module area except for tightly related headers explicitly named in the task.

Tell each implementation subagent to read:

- the requirement sections relevant to that module
- the software design sections defining that module's interface and timing
- the relevant `docs/Module/<module-name>` folder, where `<module-name>` matches the assigned module; read the converted merged markdown manual in that folder before PDFs or other original source artifacts
- `references/object-oriented-c-module-architecture.md`
- `references/embedded-development-rules.md`
- `references/config-parameter-management.md`
- `references/peripheral-callback-rules.md` when the module touches interrupts, callbacks, DMA, polling, or shared buffers
- `references/freertos-development-rules.md` when FreeRTOS is present and the module interacts with tasks, queues, semaphores, mutexes, notifications, or ISR-to-task handoff
- `references/watchdog-safe-startup-rules.md` when the module reports health, interacts with startup self-checks, reset causes, watchdog state, or safety behavior

Also tell each implementation subagent:

- implement only its assigned module code under `Module/<module-name>` plus explicitly assigned tightly related headers
- keep board-resource binding out of `Module`; concrete drivers may accept CubeMX resources through init/config structs, but project object creation and resource binding belongs in the top-level `Board` or `board` directory
- avoid changing business logic, HMI flow, unrelated framework files, shared startup flow, or unrelated callbacks
- work with existing CubeMX handles and naming rather than inventing a parallel hardware layer
- prefer HAL/CubeMX built-in functions and callbacks over custom reimplementations; for example, use HAL UART receive-to-idle DMA support when available instead of hand-rolling USART idle interrupt plus DMA length handling
- keep project-tunable parameters centralized through the project configuration pattern and inject them through config structs, init arguments, or narrow mapping code; do not make drivers depend on broad `app` headers
- do not create a second project-level configuration hub inside the module
- return changed file paths, assumptions, and any unresolved design or framework gaps

## Review Subagent Tasks

After parallel implementation completes, run parallel review on the resulting module work when practical.

Tell each review subagent to read:

- `references/automated-review-checks.md`
- `references/object-oriented-c-module-architecture.md`
- `references/embedded-development-rules.md`
- `references/config-parameter-management.md`
- `references/peripheral-callback-rules.md` if callbacks, interrupts, DMA, polling, or shared buffers are present
- `references/freertos-development-rules.md` if FreeRTOS code is present
- `references/watchdog-safe-startup-rules.md` if watchdog, health, startup self-check, reset-cause, or safe-state behavior is present

Each review must check at least:

- whether automated review checks were run first when practical
- whether every automated-check hit is judged as acceptable, needs manual review, or requires rewrite
- whether the module stays within its ownership boundary
- whether board binding is kept in a dedicated top-level `Board` or `board` directory and not mixed into `app` or concrete driver folders
- whether core interfaces remain platform-neutral and do not expose HAL, CubeMX, board, or concrete-driver details
- whether interfaces remain narrow and explicit
- whether application code depends only on abstract interfaces
- whether project-tunable parameters are centralized and traceable
- whether ISR/callback/DMA behavior is bounded and defers nontrivial work
- whether variables shared between ISR/HAL callback context and the main loop are declared `volatile` and protected further when atomicity is required
- whether watchdog refresh ownership and health reporting remain centralized when watchdog behavior is present
- whether retries, waits, buffers, queues, and loops are bounded
- whether error handling matches the design's fault strategy
- whether CubeMX integration boundaries are preserved
- whether forbidden patterns from the references appear

Automated-check hits are not automatically failures. They must be reviewed explicitly. If a hit confirms a violation, require rewrite before integration and name the violated rule and required correction.
