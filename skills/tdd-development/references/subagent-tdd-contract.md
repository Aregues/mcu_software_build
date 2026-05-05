# Subagent TDD Contract

The main orchestrator owns architecture, scope, final integration, and user decisions. A TDD subagent owns only the assigned independent slice or slice group.

## Required Input

Every subagent task must include:

- release directory and software design path
- confirmed requirements, ECR constraints, and architecture constraints
- assigned slice list with Requirement, Layer, Given/When/Then, Hardware boundary, Files likely touched, and Done condition
- allowed edit scope
- forbidden edit areas
- required reference files
- required test command
- report format

Tell workers they are not alone in the codebase, must not revert others' changes, and must adapt to existing or concurrent changes.

## Write Boundary

The subagent may edit only:

- assigned `test/` files
- assigned implementation files
- narrow build/test metadata explicitly allowed by the main orchestrator

The subagent must not edit unrelated CubeMX-generated files, shared startup, callback dispatch, public APIs, or central state machines unless that edit is explicitly assigned.

## Stop Conditions

Stop and report instead of deciding independently when:

- required design details are missing or contradictory
- the slice needs a new public API outside the assignment
- the hardware boundary cannot be mocked cleanly
- the implementation requires moving files or changing CubeMX structure
- tests require unavailable tools and no allowed fallback exists
- another slice or user change conflicts with the assigned files

## Report Format

Report:

- completed slices
- tests written or changed
- implementation files changed
- exact test command and result
- assumptions made
- blockers or unimplemented slices
- hardware or on-target verification still required
