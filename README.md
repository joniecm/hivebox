[![Dynamic DevOps Roadmap](https://img.shields.io/badge/Dynamic_DevOps_Roadmap-559e11?style=for-the-badge&logo=Vercel&logoColor=white)](https://devopsroadmap.io/getting-started/)

# HiveBox - DevOps End-to-End Hands-On Project

The project aims to cover the whole Software Development Life Cycle (SDLC). That means each phase will cover all aspects of DevOps, such as planning, coding, containers, testing, continuous integration, continuous delivery, infrastructure, etc.

### Quick Start

```bash
pip install -r requirements.txt
python -m src.app
curl http://localhost:5000/version
```

### Documentation

| Topic                                                    | Description                                                                    |
| -------------------------------------------------------- | ------------------------------------------------------------------------------ |
| [API Reference](docs/api.md)                             | All endpoint details, request/response examples, and status codes              |
| [Development Guide](docs/development.md)                 | Project structure, versioning, local setup, Docker, Taskfile, and code quality |
| [Deployment Guide](docs/deployment.md)                   | Kubernetes (kind), Helm, Grafana Agent, and security scanning                  |
| [E2E Testing with Venom](docs/e2e-testing-with-venom.md) | End-to-end API test setup, suites, and CI integration                          |
