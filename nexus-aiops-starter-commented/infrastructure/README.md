# Infrastructure Folder

<!--
WHY THIS FOLDER EXISTS
======================
Application code answers:
"What does the service do?"

Infrastructure answers:
"How do we run/deploy the service?"

Keep runtime/deployment configuration here instead of mixing it with Python code.
-->

## docker/

<!--
Use for LOCAL development.

Examples later:
- docker-compose.yml
- local PostgreSQL
- local service containers

Docker is useful because every teammate gets a repeatable environment.
-->

## kubernetes/base/

<!--
Use for reusable Kubernetes resources.

Examples later:
- namespace.yaml
- deployment.yaml
- service.yaml
- configmap.yaml

M4 will eventually interact with Kubernetes for controlled rollback/scale.
-->

## kubernetes/overlays/dev/

<!--
Use for development-specific configuration.

Example:
base says "deploy payment-service".
dev overlay can say:
- replicas = 2
- dev image tag
- dev resource limits
-->

## Why no Terraform yet?

Terraform/AWS is bonus scope for this project.

First make the P0 system work:
telemetry → anomaly → RCA → decision → remediation → validation.

Only add cloud infrastructure after P0 is stable.
