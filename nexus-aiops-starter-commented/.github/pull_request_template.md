<!--
WHY THIS FILE EXISTS
====================
GitHub automatically displays this template whenever a teammate opens a Pull Request.

It forces us to explain:
- what changed,
- why it changed,
- how it was tested,
- whether a shared contract changed,
- which module consumes the change.

That makes integration across six members much safer.
-->

## What changed?

<!-- Example: Added M4 approve/reject endpoints. -->

## Why?

<!-- Explain which project requirement this supports. -->

## How was it tested?

<!-- Example: pytest tests/test_approval.py -->

## Contract impact

<!--
Contracts connect the six modules.
Check the correct option.
-->

- [ ] No shared contract change
- [ ] Shared contract change reviewed by producer + consumers

## Integration

<!--
Which other module consumes this?
Example: M5 UI consumes M4 decision/approval state.
-->

## Checklist

- [ ] Tests pass
- [ ] `/health` still works
- [ ] Mock/real provider behavior remains compatible
- [ ] No manual JSON copy/paste was added
