# Watchdog and Safe Startup Rules

Read this file when the requirement document, software design document, CubeMX configuration, or generated code requires or includes IWDG, WWDG, startup self-check behavior, reset-cause handling, or safe-startup behavior.

## Watchdog Ownership

- Do not enable or invent watchdog behavior when the project documents and CubeMX framework do not require or include it.
- Use the CubeMX-generated watchdog handle and init path. Do not duplicate watchdog initialization manually.
- If the software design document requires a hardware watchdog but the generated CubeMX framework lacks IWDG or WWDG support, classify it as a `framework/configuration gap`.
- Do not replace a required hardware watchdog with an ad hoc software timer.
- Watchdog refresh must have one clear owner, preferably an `app`-level health monitor or system supervisor.
- Do not let unrelated `Module` drivers refresh the watchdog directly. A module may report health, but the owner decides whether system-level refresh is allowed.
- Do not refresh the watchdog directly from ISR, DMA callbacks, or low-level `Module` code unless the software design document explicitly requires it and explains why it is safe.

## Startup and Health Gate Rules

- Startup must complete the necessary self-check sequence before entering the normal watchdog refresh path.
- Refresh the watchdog only after required critical tasks or modules have reported healthy status, so a stuck or failed subsystem cannot be hidden by local refresh calls.
- Startup self-check should cover the items required by the design document, such as key sensor readiness, communication readiness, actuator safe state, configuration validity, and critical peripheral initialization result.
- Watchdog reset cause should be read, recorded, and cleared during startup when the platform supports it, then exposed to `app` or a diagnostic module for policy handling.
- Low-level drivers must not make business decisions based on watchdog reset cause.

## Timing and Configuration

- Watchdog refresh period, timeout assumptions, startup self-check timeout, and health-report deadlines are project-tunable parameters and must follow `references/config-parameter-management.md`.
- The refresh period must be less than the watchdog timeout and must leave margin for documented worst-case execution and scheduling jitter.
- Do not leave watchdog timing, health-report deadlines, or startup self-check limits as unexplained magic numbers.

## Fault Behavior

- If the fault strategy is to stop refreshing and let the watchdog reset the system, first drive outputs to the documented safe state when possible.
- If the fault strategy is degraded operation, continue refreshing only through the same centralized health-gated path.
- If watchdog owner, refresh gate conditions, startup self-check scope, reset-cause handling, or fault behavior is unclear from the design, stop and resolve the uncertainty before treating the implementation as complete.

## Review Checklist

Check these before accepting watchdog or safe-startup code:

- watchdog behavior is required by documents or present in CubeMX-generated code
- initialization uses CubeMX-generated paths
- refresh ownership is centralized
- modules report health instead of refreshing directly
- refresh is health-gated and not called from ISR/DMA callbacks
- startup self-checks match the software design
- reset-cause policy belongs to `app` or diagnostics, not low-level drivers
- refresh timing and health deadlines are centralized through project configuration
- framework gaps are classified instead of hidden by software substitutes
