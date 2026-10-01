# M4 — Decision Engine

<!--
OWNER: M4

WHY IT EXISTS
=============
Transforms a diagnosed incident into a SAFE structured action proposal.

Consumes:
- RCAResult from M3
- FinOpsContext from M6 when relevant
- runtime context

Produces:
- DecisionProposal
- ActionResult

P0 actions:
ROLLBACK
SCALE
ESCALATE

IMPORTANT:
The LLM never directly executes commands.
-->
