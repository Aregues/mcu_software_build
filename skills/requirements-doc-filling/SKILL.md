---
name: requirements-doc-filling
description: Guide users to write a project requirements document by using the ask tool section by section, formatting the result against the bundled SRS template, and saving the final markdown file under docs/Requirements. Use when Codex needs to collect project background, scope, functional requirements, non-functional requirements, HMI details, exception handling, or hardware/software constraints interactively.
---

# Requirements Doc Filling

Use this skill to collect project requirements interactively, draft a complete markdown requirements document, and save the final document under `docs/Requirements`.

Read `references/requirements-template.md` before asking questions so the final structure matches the bundled template.

Read `references/requirements-template-example.md` when preparing each question round so the user sees a realistic example for the current section.

## Workflow

1. Review the template headings and note which fields require user input.
2. For the current level-2 heading, extract the matching level-2 section from `references/requirements-template-example.md`.
3. Use the `ask` tool to show a concise example excerpt and gather information for that level-2 heading only.
4. Build the document incrementally, keeping section titles and numbering aligned with the template.
5. Return a clean markdown draft that the user can review and refine.
6. Save the final accepted draft to `docs/Requirements/<project-name>-<YY-MM-DD>.md`.

## Asking Strategy

- Prefer the `ask` tool over a long free-form prompt so the user can answer step by step.
- Ask at the granularity of one template level-2 heading per round. A level-2 heading is a `##` section such as `## 4. Non-functional Requirements`.
- Do not combine different level-2 headings in one question round. For example, ask `## 4. Non-functional Requirements` and `## 5. HMI Requirements` in separate rounds.
- Within one level-2 heading, ask for its level-3 subsections together only if the prompt remains short. If it becomes long, split by level-3 subsection while staying inside the same level-2 heading.
- Start with `## 1. Project Goals`, then proceed to `## 2. Project Scope`, `## 3. Functional Requirements`, `## 4. Non-functional Requirements`, `## 5. HMI Requirements`, `## 6. Exception and Boundary Requirements`, and `## 7. Hardware Platform and Software Architecture Constraints`.
- Do not ask about a later level-2 heading until the current one has enough information or the user explicitly chooses to skip it.
- Before asking for a level-2 heading, show a short "Example" block copied or paraphrased from the matching level-2 section in `references/requirements-template-example.md`.
- Keep examples short, but include at least one representative example for every field being requested in the current round. If a requested field is missing from the initial excerpt, extend the excerpt rather than omitting that field.
- If the example section numbering differs from the template, match by meaning first, then by number. For example, the example's `Project Background and Goals` section maps to the template's `Project Goals`.
- Make clear that the example is illustrative and should not be copied blindly.
- Ask embedded-specific follow-ups when relevant: MCU, peripherals, timing, fault handling, startup behavior, power-loss recovery, and dangerous output protection.
- When the user does not know a value, record `TBD` for unknown items and `NA` for not applicable items instead of inventing details.
- When a requirement should be measurable, prompt for a concrete threshold, timing, range, or limit.
- If an answer is vague, ask one clarification question before drafting that field.

## Example Display Rules

- For `## 1. Project Goals`, show an example with project background, project positioning if available, target users, and project goals.
- For `## 2. Project Scope`, show examples of in-scope and out-of-scope bullet lists.
- For `## 3. Functional Requirements`, show one complete function example with description, input, output, trigger, constraints, and acceptance criteria if available. If the example lacks acceptance criteria, explicitly ask the user to provide them.
- For `## 4. Non-functional Requirements`, show examples of performance, reliability, safety, maintainability, and environment/power requirements.
- For `## 5. HMI Requirements`, show examples of key definitions, pages, alerts, and operation flows.
- For `## 6. Exception and Boundary Requirements`, show examples of fault detection conditions and system behavior.
- For `## 7. Hardware Platform and Software Architecture Constraints`, show examples of MCU, memory, power, debug interface, and software layering.
- Do not show examples in the final document unless the user provided them as actual requirements.

## Output Rules

- Follow the structure and wording style of `references/requirements-template.md`.
- Preserve the numbered headings unless the user explicitly wants a trimmed version.
- Replace bracket placeholders with real content, `TBD`, or `NA`.
- Keep example sections only if the user wants them; otherwise remove example-only content from the final draft.
- Write concise, reviewable requirement statements. Avoid marketing language.
- Separate in-scope items and out-of-scope items clearly.
- For each functional requirement, include: description, input, output, trigger, constraints, and acceptance criteria.
- Do not fabricate metrics, hardware parameters, or safety behavior.

## Suggested Question Order

Ask in this exact level-2 sequence unless the user explicitly asks to skip or reorder sections.

### Round 1: `## 1. Project Goals`

Ask for:
- project background
- project positioning
- target users
- 2-3 measurable project goals

### Round 2: `## 2. Project Scope`

Ask for:
- in-scope function modules
- explicit out-of-scope items

### Round 3: `## 3. Functional Requirements`

For each function, ask for:
- function name
- description
- inputs
- outputs
- trigger conditions
- constraints
- acceptance criteria

### Round 4: `## 4. Non-functional Requirements`

Ask for:
- performance targets
- reliability strategy
- safety requirements
- maintainability requirements
- environment and power constraints

### Round 5: `## 5. HMI Requirements`

Ask for:
- HMI definitions

Use the template subsections as prompts: input devices, pages or displays, prompts and alerts, and user operation flows.

### Round 6: `## 6. Exception and Boundary Requirements`

Ask for:
- abnormal and boundary scenarios

Use the template subsections as prompts: fault detection conditions, system behavior, damaged or illegal parameters, startup initialization strategy, and power-loss recovery.

### Round 7: `## 7. Hardware Platform and Software Architecture Constraints`

Ask for:
- hardware platform
- software architecture constraints

## Finalization

- After enough information is collected, assemble the full markdown document in one pass.
- Briefly list any remaining `TBD` items after the draft.
- If the user asks for refinement, continue from the existing draft instead of restarting the interview.
- When the user accepts the draft or asks to finalize, save it to `docs/Requirements/<project-name>-<YY-MM-DD>.md`.
- Use the project name collected in section 1. If it is missing, ask for it before saving.
- Format the date as two-digit year, month, and day in the user's local timezone, for example `26-04-11`.
- Sanitize `<project-name>` for file paths: trim whitespace, replace path separators and characters invalid on Windows with `-`, collapse repeated spaces or hyphens, and keep readable Chinese or English project names.
- Create `docs/Requirements` if it does not exist.
- If the target file already exists, ask before overwriting. If the user does not want overwrite, append a short suffix such as `-v2`.
- After saving, report the saved path and list any remaining `TBD` items.
