[![Dynamic DevOps Roadmap](https://img.shields.io/badge/Dynamic_DevOps_Roadmap-559e11?style=for-the-badge&logo=Vercel&logoColor=white)](https://devopsroadmap.io/getting-started/)

# HiveBox | End-to-End DevOps Project

Production-style backend and platform project that covers practical DevOps skills across the full SDLC:
application development, observability, automated testing, containerization, Kubernetes deployment, and infrastructure as code.

## Highlights

- Flask API with real external data integration (openSenseMap) and resilient fallback behavior.
- Cache layer (Valkey / Redis-compatible) and object storage (MinIO) for persistence.
- Prometheus metrics and Grafana Agent manifests for metrics/log forwarding.
- Multi-layer automated testing: unit, integration, and end-to-end (Venom).
- Taskfile-driven workflows for linting, testing, building, and deploying.
- Deploy targets: local Kubernetes (kind), Helm chart, and cloud (AKS via Terraform).
- Clean route/service separation, background data flushing, and dependency-aware readiness checks.

## System Overview

### Core flow

1. API receives a request (for example `/temperature`).
2. Service fetches/aggregates data from openSenseMap.
3. Latest values can be served from cache (Valkey) when appropriate.
4. Buffered records are persisted to object storage (MinIO).
5. Metrics are exported to `/metrics` and can be scraped/forwarded by Grafana Agent.

### Key endpoints

- `GET /version` - application version
- `GET /temperature` - latest average temperature and status (`Too Cold`, `Good`, `Too Hot`)
- `POST /store` - flush buffered temperature data to MinIO
- `GET /metrics` - Prometheus metrics
- `GET /readyz` - readiness status for Kubernetes and health checks

## Tech Stack

| Area                       | Technologies                                  |
| -------------------------- | --------------------------------------------- |
| Backend                    | Python, Flask, Requests                       |
| Storage & Cache            | MinIO (S3-compatible), Valkey/Redis           |
| Observability              | Prometheus metrics, Grafana Agent             |
| Testing                    | Pytest (unit/integration), Venom (E2E API)    |
| Containers & Orchestration | Docker, Kubernetes (kind), Helm               |
| Infrastructure as Code     | Terraform (AKS workflow)                      |
| Developer Experience       | Taskfile automation, HTTP request collections |

## Quick Start (Local)

```bash
pip install -r requirements.txt
python -m src.app
curl http://localhost:5000/version
```

## Typical Commands

```bash
# Quality
task lint
task test:unit
task test:integration
task test:all

# End-to-end tests
task test:e2e:venom:local
task test:e2e:venom:kind

# Local app runtime
task run

# Docker
task docker:build

# Local Kubernetes
task kind:create
task kind:deploy
task kind:delete
```

## Deployment Targets

- **Local cluster:** kind manifests in `infra/`
- **Templated deployment:** Helm chart in `infra/app-chart/`
- **Cloud path:** Terraform + AKS setup in `infra/terraform/`

## Repository Map

```text
src/
	routes/       # HTTP endpoints (Blueprints)
	services/     # Business logic and integrations
	background/   # Periodic/background jobs
tests/
	unit/         # Fast isolated tests
	integration/  # API-level and integration checks
	e2e/          # Venom suites and vars
infra/
	app/          # Kubernetes manifests
	app-chart/    # Helm chart
	terraform/    # AKS IaC
```

## Documentation

| Topic                                                    | Description                                |
| -------------------------------------------------------- | ------------------------------------------ |
| [API Reference](docs/api.md)                             | Endpoints, payloads, status codes          |
| [Development Guide](docs/development.md)                 | Local setup, structure, testing, tooling   |
| [Deployment Guide](docs/deployment.md)                   | kind, Helm, Grafana Agent, security checks |
| [E2E Testing with Venom](docs/e2e-testing-with-venom.md) | End-to-end suite design and usage          |
