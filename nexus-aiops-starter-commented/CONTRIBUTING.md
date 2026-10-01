# Contributing to NEXUS

<!--
WHY THIS FILE EXISTS
====================
CONTRIBUTING.md defines HOW the 6 team members should work together in Git.

Without this file:
- everyone may use different branch names,
- people may push directly to main,
- contract changes may break other modules,
- Pull Requests may have no testing evidence.

This file is not application code.
It is a teamwork rulebook.
-->

## Before you start coding

<!--
Always work from the latest develop branch.
Do not build a large feature on an old copy of the project.
-->

```bash
git checkout develop
git pull
```

Create a branch:

```bash
git checkout -b feature/m4-state-machine
```

---

## Shared contract rule

<!--
Example:
M3 produces RCAResult.
M4 consumes RCAResult.

M3 should NOT rename "root_cause" to "cause"
without discussing it with M4.
-->

If your change modifies a shared request/response contract:

1. identify the producer,
2. identify every consumer,
3. agree on the change,
4. update fixtures/tests,
5. then merge.

---

## Pull Request checklist

<!--
A Pull Request should tell reviewers:
WHAT changed?
WHY?
HOW was it tested?
WHO consumes it?
-->

- Explain the purpose.
- Explain tests performed.
- Mention contract impact.
- Mention the downstream consumer.
- Do not merge failing tests.

---

## Commit naming

<!--
Consistent commits make Git history easier to understand.
-->

Examples:

```text
feat(m4): add incident approval endpoint
test(m2): validate anomaly contract
fix(m1): handle stale telemetry
infra(k8s): add nexus namespace
docs: explain integration workflow
```
