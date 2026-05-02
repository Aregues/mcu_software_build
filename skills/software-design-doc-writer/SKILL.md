---
name: software-design-doc-writer
description: Generate and revise an embedded software design document from the requirements skill definition, docs/releases/VERSION/requirements.md, and docs/releases/VERSION/hardware.json. Use when Codex needs to produce a first-pass software design document automatically as docs/releases/VERSION/software_design.md, refine an existing design draft with the user, or detect that current hardware connections cannot realize required software behavior and hand the issue back to the hardware-interface-writer skill after user approval.
---

# Software Design Doc Writer

Use this skill to turn an existing requirement document and hardware connection file into a structured software design document.

## Release Document Layout

Use the single-project release layout:

```text
docs/releases/<version>/
  requirements.md
  hardware.json
  software_design.md
  cubemx_build.md
  notes.md
```

If the user names a release version, use that version exactly after sanitizing it to a directory-safe name such as `v1.0`. If the user does not name a version, use the newest semantic version under `docs/releases`. If no release exists, report that `requirements.md` and `hardware.json` are missing instead of creating an empty design basis.

Read the sibling `../requirements-doc-filling/SKILL.md` file in this plugin before drafting so the software design stays aligned with the requirement-document collection logic and section semantics established by the requirements skill.

Read `references/software-design-template.md` before drafting so the output section order and headings match the bundled design-document template.

Read `references/software-design-example.md` only to constrain document format, section granularity, and writing style. Do not echo the example to the user and do not copy project-specific example content into the generated document.

## Required Inputs

- Requirement document: prefer the active release file `docs/releases/<version>/requirements.md`. Confirm the release when multiple candidates exist and the newest semantic version is not clearly intended.
- Hardware connection file: prefer the active release file `docs/releases/<version>/hardware.json` produced by the `hardware-interface-writer` skill in this plugin.

If either file is missing, ask the user to provide or identify it before drafting.

## Workflow

1. Confirm the exact requirement document and hardware connection file to use.
2. Read the requirement document and extract: project goals, scope, functional requirements, non-functional requirements, HMI or communication behavior, exception handling, hardware platform constraints, and architecture constraints.
3. Read the hardware connection file and extract: MCU or board device, connected modules, buses, timers, communication peripherals, GPIO roles, power rails, and feasibility notes or assumptions.
4. Cross-check software needs against the hardware connections before writing:
   - Ensure every required software-facing function has a realizable hardware path.
   - Check that required communication links, sensing paths, actuator outputs, timing sources, and storage assumptions are supported by the current connection file.
   - Treat stated hardware feasibility risks, voltage risks, missing pins, missing peripherals, or unresolved assumptions in the connection file as design constraints.
5. If the current hardware connections cannot support one or more required software functions, stop drafting the final design document, explain the mismatch concretely, and ask the user whether to revise hardware by using the `hardware-interface-writer` skill in this plugin.
6. Only after the user explicitly allows hardware revision, hand the task back to the hardware skill, update the hardware connection file, then resume this skill and regenerate or revise the software design document.
7. If the hardware is feasible or feasible with documented assumptions, generate the first full design draft automatically with no interactive section-by-section interview.
8. Save the generated markdown document to `docs/releases/<version>/software_design.md`.
9. When the user later asks for changes, revise the existing design document instead of restarting from scratch.

## Automatic First Draft Rules

- The first generation pass must be fully automatic. Do not interview the user section by section when a requirement document and hardware connection file already exist.
- Infer software modules, runtime mechanism, state machine, interfaces, and timing design from the supplied artifacts.
- Use `TBD` only for facts that cannot be derived safely from the requirement document, hardware connection file, or clearly stated assumptions.
- Keep assumptions explicit. Do not silently invent protocols, memory maps, task periods, parameter ranges, or fault behavior.
- Prefer concrete embedded-software structure: initialization flow, scheduling model, state transitions, module boundaries, data structures, interfaces, abnormal handling, and verification guidance.

## Embedded Design Principles

- The generated design document must explicitly state embedded-software design principles instead of leaving them implied by examples alone.
- Treat determinism, predictable timing, analyzable worst-case response, and controlled fault behavior as higher priorities than peak throughput or average-case performance.
- Treat system stability, bounded resource use, and implementation predictability as higher priorities than runtime flexibility or abstract extensibility.
- Require that performance-oriented choices preserve real-time behavior, task-period stability, interrupt responsiveness, memory bounds, and fault-handling consistency.
- Prefer static and auditable design decisions. If memory use, execution latency, queue depth, retry behavior, timeout handling, or recovery behavior is relevant, describe the chosen bounds or state `TBD` explicitly.
- Avoid vague architecture language. State what makes the design implementable on the target MCU or board under its timing, peripheral, and memory constraints.

## CubeMX Framework Alignment

- When the target project is expected to be implemented on an STM32CubeMX-generated framework, the design document must define implementation-facing architecture boundaries without duplicating the later code-implementation rules.
- Treat CubeMX-generated `Core`, `Drivers`, middleware, startup files, linker scripts, and project metadata as the base framework. The design should state that project-owned code is added around that framework rather than replacing or reorganizing it.
- Prefer a lightweight ownership model that the implementation skill can refine:
  - `app` owns business behavior, HMI flow, state machines, scheduling decisions, and project-level orchestration.
  - `Module` owns reusable module interfaces and external-device or hardware-abstraction responsibilities.
  - `Board` or `board` owns board-level resource binding, object creation, CubeMX handle injection, and concrete resource selection.
  - `Config` or `config` owns project-tunable constants, thresholds, periods, retry counts, feature switches, and calibration defaults.
- State dependency direction at a design level: business logic should depend on stable module/service abstractions, not directly on CubeMX/HAL handles, register headers, or concrete peripheral details.
- Keep this section design-level only. Do not prescribe exact C struct layouts, ops-table implementations, generated build-file edits, callback code, compiler flags, flashing flow, or subagent implementation procedures; those belong to `cubemx-code-implementation`.
- If the requirement or hardware artifacts do not justify one of the ownership layers, mention it as optional or `TBD` rather than forcing unnecessary folders.

## Drafting Rules

- Follow the section order and numbering style from `references/software-design-template.md`.
- Use `references/software-design-example.md` only as a formatting constraint and completeness check.
- Map requirement-document content into design-document sections. Expand requirements into implementable design decisions, but stay traceable to the source requirement.
- Use the hardware connection file to ground module interfaces, driver responsibilities, peripheral use, power-related precautions, and feasibility assumptions.
- When the requirement document is specific, keep the design equally specific.
- When the requirement document is broad, draft a conservative design that can be implemented on the current hardware and mark unresolved details as `TBD`.
- Do not include the example document in the final output.
- Do not claim hardware support that is absent from the connection file.
- Do not claim software features that are outside the requirement document unless they are necessary support functions such as initialization, diagnostics, parameter validation, or fault handling.
- Write design constraints, not only functional intent. Explain why the selected scheduling model, task split, interface boundaries, and fault strategy satisfy deterministic embedded behavior on the stated hardware.
- Distinguish clearly between periodic paths, interrupt-driven paths, event-triggered paths, and background or deferred paths. Make the trigger source, execution context, and timing expectation clear for each critical path.
- When describing memory, buffering, blocking behavior, concurrency, or shared data, prefer bounded and reviewable strategies. If the requirement or hardware artifacts do not justify a detail, mark it as `TBD` instead of inventing an unbounded mechanism.
- Describe how degraded operation and protective behavior work when sensors fail, communication times out, storage is unavailable, or outputs must be forced to a safe state.
- In the design-principles section, explicitly state that determinism and worst-case behavior take priority over peak performance whenever the two are in tension.
- For CubeMX-based targets, describe how the architecture maps onto `app`, `Module`, `Board` or `board`, and `Config` or `config` responsibilities at a high level, while leaving concrete file names and implementation patterns to the coding phase unless already obvious from project artifacts.
- Do not put CubeMX implementation mechanics into the design document unless they are required constraints from the requirement or hardware artifacts. It is enough to name the intended integration points, owned layers, and dependency boundaries.

## Feasibility Escalation Rules

Treat the design as blocked when any of the following is true:

- A required sensor, actuator, display, storage path, or communication path is missing from the hardware connection file.
- A required timing or peripheral resource cannot be mapped from the connection file.
- The connection file itself records assumptions or risks that would prevent reliable implementation of the requirement.
- Power, voltage, or electrical notes in the connection file make a required software-controlled function unsafe or undefined.

When blocked:

1. Name the exact requirement that is unsupported.
2. Name the exact hardware gap or contradiction.
3. State the impact on software design.
4. Ask whether to revise hardware through the `hardware-interface-writer` skill in this plugin.

Do not modify hardware artifacts without the user's permission.

## Revision Rules

- When the user asks for changes after a draft exists, edit the existing design document in place.
- Preserve the established section numbering unless the user requests a restructure.
- Update only the affected sections plus any downstream dependencies such as interfaces, timing, state machine, storage, or test advice.
- Keep prior confirmed content unless it is superseded by the user's new request or by corrected hardware constraints.
- After each revision, summarize what changed and list any remaining assumptions or open items.

## Output Rules

- Save the final markdown to `docs/releases/<version>/software_design.md`.
- Create `docs/releases/<version>` if it does not exist.
- Use the active release version from the user's request or the Release Document Layout rules above.
- If the target file already exists, inspect it before overwriting. If the user asked to update that document, revise it in place. If a new draft is needed and overwrite is not confirmed, create or use a new release directory such as `v0.2` instead of adding date or project suffixes to the filename.
- After saving, report the path used, the requirement document used, the hardware connection file used, and any remaining `TBD` items or assumptions.

## Recommended Section Mapping

Use this mapping as a checklist while drafting:

- Requirement goals and non-functional targets -> section 2 and its subsections.
- Functional requirements -> sections 3, 8, 9, and 10.
- Runtime or timing constraints -> sections 4 and 11.
- Parameters, status, telemetry, cached values -> sections 5 and 6.
- Exception and boundary behavior -> sections 7 and 12.
- Hardware and architecture constraints -> section 2.3 plus sections 10 and 13.
- Section 2.2 must explicitly state embedded design principles such as determinism over peak performance, avoidance of uncontrolled runtime behavior, and resource-bounded design decisions.
- Section 2.3 should map the design to the expected CubeMX-based ownership layers when applicable: generated framework, `Module`, `Board` or `board`, `Config` or `config`, and `app`.
- Section 4 must explain task periods, trigger sources, execution contexts, ordering or priority relationships, and worst-case response expectations for control, protection, and communication paths.
- Sections 5 and 6 must describe static resource assumptions, buffer or storage boundaries, and how shared state is updated or protected across contexts.
- Sections 7 and 12 must describe timeout handling, communication abnormal cases, sensor invalidity, degraded operation, protective actions, and the conditions for recovery or manual intervention.
- Section 10 should identify which interactions are abstract module/service interfaces and which depend on board-level resources, without specifying detailed C implementation mechanics.
- Section 13 should give a concise CubeMX-friendly directory ownership suggestion, including `app`, `Module`, `Board` or `board`, and `Config` or `config` when applicable.

## Quality Checks Before Saving

- Every major required function has an owning software module.
- Runtime periods, interrupts, polling, or task triggers are consistent with the hardware and requirement constraints.
- Module interfaces match the peripherals and modules named in the hardware connection file.
- Fault handling covers requirement-document exceptions and hardware-noted risks that affect software behavior.
- The design document reads as an implementation guide, not a restatement of requirements alone.
- The document explicitly states determinism-oriented design principles instead of relying only on generic principles such as modularity or maintainability.
- The worst-case response path for key control and protection behavior is explained well enough to review for plausibility.
- Any use of dynamic memory, blocking waits, retries, deferred processing, or variable-latency behavior is either explicitly justified and bounded or explicitly marked `TBD`.
- Resource limits and interface boundaries are reviewable: memory assumptions, buffer ownership, queue depth, persistent-storage use, and cross-context data exchange are not left ambiguous when they affect behavior.
- Fault entry conditions, the resulting software state, the trigger owner, response timing, and recovery conditions are described for major abnormal cases.
- For CubeMX-based targets, the design leaves a clear route to implementation: generated framework boundaries are preserved, project-owned logic has a documented home, board-resource binding is separate from business behavior, and tunable parameters have an identified owner.
- The design does not overstep into implementation-only details such as exact driver object layout, callback body code, generated project-file edits, build commands, flashing commands, or subagent task plans.
