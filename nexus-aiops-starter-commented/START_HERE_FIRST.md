# START HERE FIRST

<!--
WHY THIS FILE EXISTS
====================
This is the learning entry point for the commented starter repository.

If the repository feels overwhelming, do NOT read every file randomly.
Follow the order below.
-->

## Read in this order

1. `README.md`
   - understand the complete project.

2. `docs/TEAM_WORKFLOW.md`
   - understand how 6 people work in parallel.

3. `docs/INTEGRATION_CONTRACT.md`
   - understand why contracts and mocks matter.

4. `mocks/README.md`
   - understand the anti-waiting strategy.

5. If you are M4:
   `docs/M4_START_HERE.md`

6. Then inspect:
   `services/shared-nexus-api/`

7. Only after that:
   infrastructure, observability, CI/CD.

---

## What should exist on Day 1?

You do NOT need a complete application.

You need:

```text
repository
+ contracts
+ mocks
+ ownership
+ FastAPI skeleton
+ state machine
+ team Git workflow
```

---

## How to use comments

Most files start with comments such as:

```text
WHY THIS FILE EXISTS
WHO USES IT
WHAT IT DOES
```

Read those comments before editing the file.

For JSON:
- `.json` = executable
- `.jsonc` = learning/commented copy
