# Master Prompt: Build the Complete NEXUS Beginner-to-Advanced Book

## What this file is

This is not the NEXUS book. This is the master prompt that tells an AI coding
tool how to investigate this repository and write the book.

The final deliverable must be one large reference book:

`docs/learning/NEXUS_COMPLETE_BEGINNER_TO_ADVANCED_BOOK.md`

The book is meant to be studied later with another AI. It must therefore be
self-contained, accurate, deeply connected to the real code, and understandable
to a complete beginner.

## How Galal should use this prompt

Open the NEXUS repository in an AI coding tool that can read the complete local
repository. Then send this message:

> Read `docs/learning/GENERATE_NEXUS_COMPLETE_BOOK_PROMPT.md` completely. Follow
> it exactly. Start with Phase 0 only. Do not modify application code, commit,
> push, merge, or operate the Kubernetes cluster.

When the AI finishes a phase, use:

> Read the master prompt and `_BOOK_BUILD_STATE.md` again. Continue with the next
> unfinished book-building phase. Write real book content, not a plan or summary.

If a session runs out of context, start a new session and use the same continue
message. For the final audit, use a new AI session and say:

> Read the master prompt, the build-state file, and the complete generated book.
> Perform Phase 7 as an independent accuracy and completeness audit. Repair the
> book directly, but do not change project code.

Do not paste this prompt into a plain web chat without the repository. The AI
must be able to inspect the files and current Git revision.

---

# Instructions For The Book-Building AI

## 1. Your role

You are simultaneously:

- a patient teacher for a complete beginner;
- a senior Site Reliability Engineer;
- a platform and Kubernetes engineer;
- a Python and FastAPI engineer;
- an observability engineer familiar with Prometheus, Grafana, Loki, and Alloy;
- an ML engineer able to explain anomaly detection honestly;
- a distributed-systems reviewer;
- a security-minded incident-response engineer;
- a FinOps engineer;
- a technical book author and accuracy auditor.

Your task is not to redesign NEXUS and not to impress the reader with jargon.
Your task is to discover what the current repository actually does and write a
complete project-based learning book that teaches it from zero to an advanced
technical understanding.

## 2. The student

The primary reader is Galal, the team lead and M1 owner. Treat him as a complete
beginner. Do not assume that he already understands:

- source code versus a running process;
- files, folders, paths, terminals, and commands;
- localhost, IP addresses, ports, clients, and servers;
- HTTP, URLs, endpoints, GET, POST, request bodies, responses, and status codes;
- JSON, APIs, schemas, types, validation, or environment variables;
- Python packages, imports, functions, classes, async code, or exceptions;
- Git, branches, commits, remotes, pushes, pull requests, or merges;
- containers, images, volumes, networks, Docker Compose, or health checks;
- Kubernetes Pods, Deployments, Services, ConfigMaps, Secrets, RBAC, PVCs, and
  rollouts;
- metrics, logs, PromQL, LogQL, SLOs, baselines, or recovery windows;
- anomaly detection, z-scores, correlation, precision, recall, or false alarms;
- root-cause analysis, state machines, guardrails, idempotency, leases, fencing,
  retries, circuit breakers, or outboxes;
- RAG, LLMs, retrieval, provenance, FinOps, rightsizing, or cost models.

The student wants understanding, not memorization and not a fake claim of having
written every line manually. The book must make him able to run, explain, debug,
demo, and defend the project in front of an examiner.

Use simple English. For especially difficult ideas, add a short optional Egyptian
Franco-Arabic note using Latin characters only. Do not use Arabic script. Never
use a difficult term before defining it.

## 3. Final output and working files

The final book must be written to exactly:

`docs/learning/NEXUS_COMPLETE_BEGINNER_TO_ADVANCED_BOOK.md`

Maintain a resumable working ledger at:

`docs/learning/_BOOK_BUILD_STATE.md`

The ledger is not a substitute for the book. It records:

- the pinned commit hash and branch;
- whether the working tree was clean;
- inventory counts;
- chapters completed and audited;
- files documented;
- endpoints, environment variables, queries, formulas, tests, and Kubernetes
  resources found versus documented;
- open questions and contradictions;
- the exact next task under a `RESUME FROM` heading.

Only write under `docs/learning/`. Never edit project source, tests, configuration,
manifests, evidence, or existing reports. Never commit, push, merge, checkout,
reset, stash, delete, or rewrite Git history. Never operate Docker or Kubernetes
unless Galal separately gives explicit permission.

## 4. Required scale and quality

This must be a real book, not a long README and not a collection of shallow
summaries.

Target a minimum of 35 substantial chapters plus appendices. Aim for roughly
40,000 to 70,000 useful words if the repository supports that depth. Do not add
padding to reach a number. Depth must come from explaining the real system,
worked examples, code journeys, failure cases, diagrams, references, and labs.

The final book must:

- have a linked table of contents;
- move strictly from beginner foundations to advanced internals;
- explain the complete end-to-end system before isolated implementation details;
- cover every major directory and every runtime component;
- include every tracked source, test, config, manifest, script, UI, contract, and
  mock file in a file catalog;
- document every public API endpoint;
- document every meaningful environment variable and default;
- document every PromQL, LogQL, and important SQL query;
- document every state and transition in the incident workflow;
- document every important threshold, timeout, interval, retry count, port,
  resource limit, and model parameter;
- show actual request and response examples derived from the real schemas;
- explain the two real scenarios: faulty deployment with rollback, and traffic
  spike with scaling;
- explain safe failure paths where the platform refuses to act;
- map tests to behavior and explain what tests do not prove;
- distinguish demo-ready from production-ready;
- include a glossary and an examiner question bank with answers.

Do not use phrases such as `self-explanatory`, `obvious`, `the rest is similar`,
`and so on`, or `etc.` to avoid documenting something.

## 5. Truth and evidence rules

### 5.1 Pin the code version

At the start, inspect and record:

- `git rev-parse HEAD`;
- `git branch --show-current`;
- `git status --short`;
- recent Git history.

This prompt was created when `main` pointed to commit
`cfb047fd261e6c76b3c4aff97bcfec8d5bf378eb`, but that is context, not authority.
Always document the commit currently checked out when the book is generated.

### 5.2 Code is the primary source of truth

Use this priority order:

1. current executable code and manifests;
2. current tests;
3. current configuration and contracts;
4. recorded runtime evidence;
5. recent reports and runbooks;
6. old planning documents and old learning material.

If documentation disagrees with code, explain the code behavior and include the
disagreement in a `Documentation versus code` table.

The existing `docs/learning/00_inventory.md`, `_COVERAGE.md`, and older masterclass
prompt describe earlier revisions. They may help with discovery, but they must not
be copied as current truth without verification.

### 5.3 Cite every project-specific claim

Every claim about NEXUS behavior must cite a current source using repository path
and line numbers, for example:

`services/telemetry-intelligence/app/telemetry.py:L40-L78`

General explanations such as what HTTP means do not need repository citations.
Code excerpts must be short, carry a path and line range, and be explained line by
line when they are important.

### 5.4 Never invent

If something cannot be proven from the repository or observed safely, say one of:

- `NOT FOUND IN THE REPOSITORY`;
- `INFERRED, NOT EXPLICITLY DOCUMENTED`;
- `EXPECTED FROM STATIC READING, NOT EXECUTED`;
- `OBSERVED BY RUNNING A SAFE CHECK`.

Never invent ownership, rationale, runtime output, test results, model accuracy,
cost savings, incident results, or production readiness.

### 5.5 Protect secrets

Never copy a secret, password, API key, token, or connection password into the
book. Document the variable name, purpose, and where it is supplied, but replace
the value with `<redacted>`.

## 6. Discovery scope

Inspect the whole tracked repository, excluding Git internals, caches, generated
bytecode, local AI worktrees, and the book files themselves. At minimum inspect:

- `README.md`;
- `apps/demo-microservices/`;
- `services/telemetry-intelligence/`;
- `services/anomaly-engine/`;
- `services/root-cause-analysis/`;
- `services/shared-nexus-api/`;
- `services/incident-memory/`;
- `services/finops-engine/`;
- `shared/`;
- `contracts/`;
- `config/`;
- `mocks/`;
- `observability/`;
- `infrastructure/`;
- `scripts/`;
- `ui/`;
- `tests/` and every service test directory;
- `.github/workflows/`;
- current reports, runbooks, integration docs, and selected evidence under
  `docs/evidence/`.

Do not waste book space walking through binary data, caches, or thousands of
repetitive evidence lines. Catalog them and deeply explain representative evidence
that proves important behavior.

## 7. Architecture that must be verified

The repository is expected to contain the following runtime roles. Treat this as
a discovery checklist, not guaranteed truth:

| Role | Expected component | Expected local port |
|---|---|---:|
| Demo workload | payment-service | 8000 |
| M1 | telemetry-intelligence | 8001 |
| M2 | anomaly-engine | 8002 |
| M3 | root-cause-analysis | 8003 |
| M4 and shared workflow API | shared-nexus-api | 8004 |
| M5, Copilot, and UI | incident-memory | 8005 |
| M6 | finops-engine | 8006 |
| Dashboard | Grafana | 3000 |
| Metrics store | Prometheus | 9090 |
| Log store | Loki | 3100 |
| Log collector | Grafana Alloy | 12345 |
| Durable relational store | PostgreSQL | 5432 inside its network |

Verify every name, port, dependency, health check, provider mode, network path,
volume, and deployment from the current Compose and Kubernetes files.

The book must eventually prove or correct this conceptual flow:

```text
User traffic
  -> payment-service
  -> metrics exposed to Prometheus
  -> structured logs collected by Alloy and stored in Loki
  -> M1 normalizes metrics, logs, Kubernetes state, baselines, and evidence
  -> M2 polls M1, detects anomalies, correlates readings, and hands off incidents
  -> M4 owns the durable incident workflow
  -> M3 scores evidence and identifies a likely root cause
  -> M6 supplies cost and scaling context when relevant
  -> M4 creates a guarded proposal
  -> a human reviews it through M5/UI and approves or rejects it
  -> M4 executes only an allowlisted Kubernetes action
  -> M1 measures post-action recovery and SLO restoration
  -> M4 resolves, fails, or escalates the incident
  -> M5 stores the terminal incident and answers grounded questions
```

Explain exactly where the real code differs from this idealized flow.

## 8. Teaching method required in every chapter

For every important concept, component, algorithm, and file, use this sequence:

1. **Beginner picture:** explain it using a concrete everyday scenario.
2. **Precise definition:** give the correct technical meaning.
3. **Why NEXUS needs it:** connect it to a real project problem.
4. **Where it lives:** cite the exact files and lines.
5. **How execution flows:** describe the order of calls and data movement.
6. **Input and output:** show a realistic example.
7. **What can fail:** include bad input, missing dependency, stale data, timeout,
   restart, concurrency, and security cases where relevant.
8. **How the code responds:** explain status codes, retries, state transitions,
   fallback behavior, and persisted evidence.
9. **Why this approach:** describe tradeoffs and realistic alternatives.
10. **How to prove it:** identify the test, check, log, metric, or evidence file.
11. **Exam answer:** provide a two- or three-sentence answer Galal can say aloud.
12. **Checkpoint:** include a small exercise and questions with answers hidden
    under Markdown `<details>` blocks.

An analogy must always be followed by the precise explanation. Never leave the
student with only the analogy.

## 9. Explain code without overwhelming the beginner

Use three levels for code explanations:

- **Level 1, map:** what the file or function contributes to the system.
- **Level 2, flow:** what happens in order and what data changes.
- **Level 3, internals:** important branches, algorithms, concurrency, validation,
  and failure handling.

For core files, explain every class and function. For small core functions, explain
important lines. For tests, explain setup, action, assertion, and what behavior the
test proves. For repetitive schemas or evidence files, list every field and deeply
walk through representative examples rather than repeating identical prose.

Every formula must have a numeric worked example. This includes, when present:

- rates and ratios;
- P95 latency;
- baseline percentiles and SLO multipliers;
- z-scores and anomaly scores;
- correlation windows;
- precision, recall, and false-positive counts;
- confidence scoring for root causes;
- scaling calculations;
- resource utilization ratios;
- cost deltas and rightsizing;
- recovery time and sustained recovery windows;
- retry backoff and timeout calculations.

## 10. Required book structure

Use the following structure. Add subsections when the repository requires them,
but do not remove a chapter.

### Front matter

1. Title page, documented commit, branch, date, and truth labels.
2. How to use the book alone and with another AI.
3. Learning map from beginner to team lead.
4. Linked table of contents.
5. One-page NEXUS story in the simplest possible language.

### Part I: Foundations from zero

6. Files, source code, running processes, memory, and the operating system.
7. The terminal, current directory, paths, commands, output, and exit codes.
8. Client/server, localhost, IP addresses, DNS, ports, sockets, and processes.
9. HTTP, URLs, endpoints, methods, headers, JSON bodies, and status codes.
10. APIs, contracts, schemas, validation, timestamps, IDs, and units.
11. Python essentials used here: modules, imports, functions, classes, type hints,
    exceptions, context managers, threads, async/await, and dependency injection.
12. FastAPI, Uvicorn, Pydantic, middleware, lifespan, routes, and OpenAPI docs.
13. Git for this project: working tree, branch, commit, remote, push, PR, review,
    merge, conflicts, and why force-push is dangerous.
14. Metrics, logs, traces, health, readiness, SLI, SLO, and incident basics.

### Part II: Runtime and platform foundations

15. Docker images, containers, layers, users, ports, networks, volumes, builds,
    health checks, and Docker Compose profiles.
16. Kubernetes from zero: cluster, node, namespace, Pod, Deployment, ReplicaSet,
    Service, ConfigMap, Secret, ServiceAccount, RBAC, PVC, probe, rollout, and
    resource requests/limits.
17. PostgreSQL and persistence: tables, rows, transactions, constraints, indexes,
    connection strings, durability, and why in-memory state is different.
18. Reliability concepts used by NEXUS: timeout, retry, backoff, idempotency,
    optimistic concurrency, lock, lease, fencing token, circuit breaker, queue,
    worker, outbox, reconciliation, fail-open, and fail-closed.

### Part III: NEXUS as one system

19. The problem NEXUS solves and the Observe-Orient-Decide-Act loop.
20. Current repository map and ownership map.
21. Static architecture diagram, runtime deployment diagram, and data-flow diagram.
22. Complete healthy request journey from browser/traffic generator to stored
    telemetry and dashboard.
23. Shared contracts, Pydantic models, JSON schemas, mocks, compatibility, and
    why a contract is not the same as stored data.
24. Shared configuration, service registry, structured logging, provider modes,
    and dependency wiring.
25. The payment-service demo workload, healthy v1, faulty v2, instrumentation,
    structured logs, and traffic generation.

### Part IV: Module deep dives

26. M1 Telemetry Intelligence.
    Cover payment metrics, Prometheus scraping, PromQL, Loki, Alloy, LogQL,
    Grafana, snapshot and window normalization, freshness, Kubernetes evidence,
    baseline measurement, evidence capture, storage, recovery validation,
    bad-deployment rules, traffic-spike rules, and all M1 endpoints and tests.

27. M2 Anomaly Detection and Correlation.
    Cover polling, feature construction, frozen reference data, z-scores, baseline
    rules, Isolation Forest's actual role, per-replica load, correlation, evidence
    refresh, incident handoff, bounded dispatch queues, retry sweeps, false
    positives, evaluation tools, all endpoints, tests, and honest ML limits.

28. M3 Root Cause Analysis.
    Cover real versus mock providers, evidence bundle creation, freshness,
    deployment scoring, traffic scoring, confidence, deterministic selection,
    unknown results, error handling, all endpoints, and tests. Clearly explain
    whether any LLM is involved in M3.

29. M6 FinOps.
    Cover M1 telemetry input, Kubernetes or explicit resource configuration,
    utilization, rightsizing, scale options, registry limits, cost assumptions,
    risk labels, persistence, recommendations, all endpoints, and tests. Separate
    demo estimates from real cloud billing.

30. M4 Decision Engine and Controlled Self-Healing.
    Cover incident ingest, authentication, state machine, diagnosis workflow,
    providers, decision rules, proposal creation, confidence threshold, FinOps
    selection, proposal TTL and digest, approvals, guardrails, service registry,
    allowlisted rollback and scale actions, preconditions, kubectl execution,
    per-incident locking, optimistic revisions, PostgreSQL workflow storage,
    writer lease and fencing, restart reconciliation, recovery workers, audit,
    provenance, archive outbox, all endpoints, and tests.

31. M5 Incident Memory, Copilot, and UI.
    Cover immutable incident memory, SQLite versus PostgreSQL, retrieval scoring,
    tags and keyword overlap, provenance, grounded answers, optional external LLM
    behavior, why this is not automatically vector-database RAG, action drafts,
    operator authentication boundary, approval forwarding, archive behavior,
    UI overview and incident pages, browser storage, all endpoints, and tests.

### Part V: End-to-end project-based scenarios

32. Scenario A: establish a healthy baseline under real traffic.
33. Scenario B: inject faulty v2, detect it, diagnose it, approve rollback,
    validate recovery, archive it, and answer a Copilot question.
34. Scenario C: create a traffic spike, detect it, calculate scale options,
    approve scale, validate sustained recovery under load, and archive it.
35. Scenario D: safe failures, including stale or missing evidence, no deployment
    event, unknown RCA, expired proposal, wrong digest, bad token, changed live
    workload, dependency outage, M5 outage, M4 restart, and failed recovery.

For each scenario include:

- a timeline;
- a sequence diagram;
- exact component-to-component calls;
- representative payloads;
- incident states;
- human decision points;
- data persisted at each stage;
- logs and metrics to inspect;
- expected failure handling;
- evidence that proves the result;
- a simple version and an examiner-level version.

### Part VI: Operations, verification, and engineering judgment

36. Local Compose startup and why its remediation actuator is intentionally mock.
37. Isolated kind/Kubernetes deployment, image loading, Secrets, RBAC, PVCs,
    port-forwarding, and safe demo operation.
38. Health, live, and ready endpoints; what each proves and does not prove.
39. Testing pyramid and complete test map: unit, contract, integration,
    PostgreSQL, UI, image build, Compose validation, and live cluster evidence.
40. CI workflow jobs, triggers, gates, and the difference between configured CI
    and an observed passing remote run.
41. Troubleshooting decision tree and runbook for common failures.
42. Security and safety review: trust boundaries, credentials, operator approval,
    network exposure, non-root containers, RBAC, missing TLS/OIDC, and threat cases.
43. Performance, concurrency, reliability, and data-consistency review.
44. Design decisions and alternatives: why each major approach was chosen or,
    when intent is not recorded, what can only be inferred.
45. Honest limitations, technical debt, demo readiness, and production gaps.
46. What Claude/AI changed versus what Git can actually prove. Explain authorship,
    review responsibility, and how Galal can honestly describe his contribution.

### Part VII: Reference appendices

47. Complete file catalog. Every tracked relevant file gets a purpose, owner or
    module, runtime status, important dependencies, and study priority.
48. Class and function index for all project Python and JavaScript source files.
49. Complete API catalog with method, path, owner, input, output, errors, auth,
    caller, and tests.
50. Complete port, container, service, image, volume, and network catalog.
51. Complete environment-variable and configuration catalog with defaults,
    units, validation, secret status, and consumers.
52. Complete contract and field dictionary with type, unit, producer, consumer,
    required/optional status, and example.
53. PromQL, LogQL, and important SQL query catalog with line-by-line explanations.
54. Kubernetes resource and RBAC catalog.
55. State-machine transition table, action guardrail table, retry/timeout table,
    and persistence table.
56. Dependency catalog: what every external package does and where it is used.
57. Test catalog mapped to requirements and known gaps.
58. Runtime evidence catalog: what each evidence set proves and does not prove.
59. Glossary from absolute beginner terms to advanced distributed-systems terms.
60. At least 150 viva/exam questions with concise answers, grouped beginner,
    intermediate, advanced, module-owner, team-lead, debugging, and challenge.
61. A progressive 14-day study plan with reading, hands-on labs, checkpoints,
    teach-back exercises, and mock defense sessions.

## 11. Diagrams required

Use valid Mermaid and also include a plain-text explanation after every diagram.
At minimum include:

- context diagram;
- container/runtime diagram;
- Compose dependency diagram;
- Kubernetes deployment diagram;
- metrics path;
- logs path;
- healthy request sequence;
- faulty deployment sequence;
- traffic spike sequence;
- M2 detection pipeline;
- M3 evidence and scoring flow;
- M4 state machine;
- approval and remediation sequence;
- recovery-validation sequence;
- M5 archive and Copilot sequence;
- database ownership diagram;
- trust-boundary diagram;
- restart/reconciliation sequence;
- source-code dependency map.

Diagrams must match the current code, not only the original project proposal.

## 12. File documentation tiers

Assign every relevant file one tier in the build ledger:

- **Tier A, core runtime:** explain every class and function, major branches,
  inputs, outputs, state changes, failures, callers, callees, and tests.
- **Tier B, supporting runtime or test:** explain every class/function/test and
  deeply explain non-obvious sections.
- **Tier C, declarative or data:** explain every field/resource/key and its role;
  use representative records for large evidence sets.
- **Catalog only:** generated cache, package marker, or repetitive evidence;
  include it in the catalog with a clear reason for not expanding it.

At minimum, FastAPI entrypoints, service/orchestration logic, algorithms,
providers, storage, contracts, Docker/Compose, Kubernetes, observability config,
shared registry, UI behavior, and integration tests must be Tier A or B.

## 13. Commands and labs

Commands are teaching material. Before every command, explain:

- what program is being called;
- what each argument means;
- which directory it must run from;
- what it reads or changes;
- what successful output looks like;
- common errors and their meaning;
- whether it is safe/read-only or state-changing.

Never tell a beginner to paste a destructive command without a warning and an
explicit confirmation step. Do not run state-changing commands while generating
the book.

Labs should progress from reading and harmless requests to controlled local and
isolated-cluster exercises. Each lab needs prerequisites, goal, commands, expected
observations, cleanup, troubleshooting, and questions.

## 14. Required comparisons and misconceptions

Explicitly correct at least these common misunderstandings:

- source code versus a running service;
- port versus endpoint;
- endpoint versus Python function;
- GET versus POST;
- metric versus log;
- Grafana versus Prometheus versus Loki versus Alloy;
- Docker image versus container;
- container versus Pod;
- Deployment versus Service;
- liveness versus readiness versus real functional health;
- anomaly versus incident versus symptom versus root cause;
- high latency versus faulty deployment;
- rollback versus restart;
- vertical scaling versus horizontal scaling;
- action success versus recovery success;
- baseline versus threshold versus SLO;
- mock provider versus real provider;
- deterministic rules versus machine learning versus an LLM;
- keyword retrieval versus embedding/vector RAG;
- contract versus database model versus API response;
- authentication versus authorization;
- concurrency lock versus database transaction versus fencing lease;
- retry versus idempotency versus reconciliation;
- demo-ready versus production-ready.

## 15. Book-building phases

Do not attempt the whole book in one response. Work directly in the files and
complete these phases in order.

### Phase 0: Freeze and inventory

Read the current repository. Create `_BOOK_BUILD_STATE.md`. Pin the commit. Count
and classify files, classes, functions, endpoints, environment variables,
contracts, queries, Kubernetes resources, tests, and evidence sets. Produce the
planned table of contents in the book. Do not write shallow chapter content yet.

### Phase 1: Foundations

Write front matter and Parts I and II. Verify every foundation against how NEXUS
uses it. Update the ledger and `RESUME FROM`.

### Phase 2: Whole-system architecture

Write Part III with verified diagrams, real paths, contracts, runtime wiring, and
the healthy request journey. Update the ledger.

### Phase 3: M1, M2, and M3

Write Chapters 26 through 28 at deep implementation level. Include algorithms,
queries, endpoints, providers, storage, tests, and failure behavior. Update the
ledger.

### Phase 4: M6, M4, and M5/UI

Write Chapters 29 through 31. Spend extra care on M4 state, concurrency, safety,
approval, persistence, recovery, and M5 provenance/operator boundaries. Update
the ledger.

### Phase 5: End-to-end scenarios

Write Part V using current code and genuine recorded evidence. Clearly label
observed evidence versus expected behavior. Update the ledger.

### Phase 6: Operations and appendices

Write Parts VI and VII. Complete every inventory counter. Add the full file,
function, API, config, query, resource, test, evidence, glossary, viva, and study
plan appendices. Update the ledger.

### Phase 7: Independent audit and repair

Prefer a fresh AI session. Re-scan the pinned revision and audit every project-
specific claim, citation, counter, link, diagram, endpoint, number, and example.
Check that the book explains both what works and what remains limited. Repair the
book directly. Mark the ledger complete only when every found item is documented
or intentionally catalog-only with a reason.

## 16. Completion gates

The book is not complete until all of these are true:

- A complete beginner can explain where NEXUS runs and what happens after one
  `/pay` request.
- The complete end-to-end incident lifecycle is traceable through real files and
  payloads.
- Every module has a beginner explanation and an advanced implementation deep
  dive.
- Every relevant tracked file appears in the file catalog.
- Every endpoint, configuration key, contract, query, state, action, and important
  formula appears in a reference table.
- Every important number has a source, unit, meaning, and change impact.
- Every major failure path explains whether the platform retries, refuses,
  escalates, reconciles, or fails closed.
- Real, mock, expected, inferred, and observed behavior are never mixed.
- All code-specific statements have valid citations for the pinned commit.
- The two live incident stories are documented without exaggerating what their
  evidence proves.
- Security, concurrency, persistence, test gaps, and production limitations are
  explained honestly.
- The linked table of contents, internal links, code paths, and Mermaid diagrams
  have been checked.
- The final chapter provides a practical route for Galal to study and defend the
  system rather than merely read it.

## 17. Required first response

After reading this prompt, do not give a generic plan in chat and do not start
teaching. Say briefly that you understand the output and safety constraints, then
execute Phase 0 by reading the repository and writing the inventory, build ledger,
and book table of contents. Report only:

- the pinned commit and branch;
- the output file paths created or updated;
- high-level inventory counts;
- contradictions or blockers that need Galal's decision;
- the exact next phase.

The durable work belongs in the Markdown files, not in a long chat response.

