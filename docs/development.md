# Development Guide

## Project Structure

```
hivebox/
├── src/                        # Application source code
│   ├── __init__.py
│   ├── app.py                  # Flask application
│   ├── sensebox_service.py     # SenseBox API integration
│   └── version.py              # Version information
├── tests/                      # Test files
│   ├── unit/                  # Unit tests
│   │   └── test_app.py
│   └── integration/           # Integration tests
│       └── test_integration.py
├── infra/                      # Infrastructure configuration
│   └── kind-config.yaml
├── .github/                    # GitHub workflows
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── .dockerignore
├── .gitignore
├── sonar-project.properties
├── Dockerfile
└── README.md
```

---

## Versioning

This project follows Semantic Versioning 2.0.0 (https://semver.org).

- Version numbers are stored in `src/version.py`
- Releases are tagged as `vMAJOR.MINOR.PATCH`
- Breaking changes increment MAJOR
- New features increment MINOR
- Bug fixes increment PATCH

---

## How to Run Locally

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run as web server

Run the Flask web application:

```bash
python -m src.app
```

The server will start on `http://0.0.0.0:5000`. You can then access the `/version` endpoint:

```bash
curl http://localhost:5000/version
```

### Run as CLI (print version)

To print the version and exit:

```bash
python -m src.app --version
```

### Run tests

All tests:

```bash
pytest tests/ -v
```

Unit tests only:

```bash
pytest tests/unit/ -v
```

Integration tests only:

```bash
pytest tests/integration/ -v
```

---

## How to Run Using Docker

This repository includes a `Dockerfile` that runs the Flask web application.

Build the image:

```
docker build -t hivebox:latest .
```

Run the container:

```
docker run --rm -it -p 5000:5000 hivebox:latest
```

Then access the version endpoint:

```bash
curl http://localhost:5000/version
```

---

## Using Taskfile for Common Workflows

This project includes a [Taskfile](https://taskfile.dev) to standardize and simplify common development workflows. Task is a modern task runner / build tool that serves as an alternative to Makefile.

### Install Task

**macOS:**

```bash
brew install go-task
```

**Linux:**

```bash
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin
```

**Windows:**

```powershell
choco install go-task
```

Or install with Go:

```bash
go install github.com/go-task/task/v3/cmd/task@latest
```

For other installation methods, see the [official installation guide](https://taskfile.dev/installation/).

### Available Tasks

List all available tasks:

```bash
task -l
```

Common tasks:

```bash
# Install dependencies
task install

# Run linter
task lint

# Run tests
task test:unit              # Unit tests only
task test:integration       # Integration tests only
task test:all              # All tests

# Run app locally
task run                   # Run Flask app with local MinIO config

# Docker operations
task docker:build          # Build Docker image
task docker:run            # Run container locally
task docker:start-infra    # Start local MinIO container
task docker:stop-infra     # Stop local MinIO container

# Kind (local Kubernetes) operations
task kind:create                    # Create kind cluster
task kind:create-with-kubeconfig    # Create cluster and save kubeconfig
task kind:load                      # Build and load image into kind
task kind:load-restart              # Load image and restart deployment
task kind:deploy                    # Build, load, and deploy everything
task kind:delete                    # Delete kind cluster

# View logs
task kind:logs-app         # Application logs
task kind:logs-minio       # MinIO logs
```

### Quick Start with Task

**Local development:**

```bash
# Install dependencies and run tests
task install
task test:all

# Run locally
task run

# Access the app
curl http://localhost:5000/version
```

**Kubernetes deployment:**

```bash
# Create cluster and deploy
task kind:create
task kind:deploy

# Access the app
curl http://localhost:4080/version

# View logs
task kind:logs-app

# Clean up
task kind:delete
```

---

## Code Quality & Linting

This project uses automated linting tools to maintain code quality and consistency.

### Python Linting with flake8

**flake8** checks Python code for style violations and programming errors.

**Install:**

```bash
pip install flake8==7.3.0
```

**Run locally:**

```bash
# Check all Python files
flake8 .
```

**Auto-fix issues:**

flake8 only reports issues. Use these tools to automatically fix them:

```bash
# Install auto-formatting tools
pip install black autopep8 ruff

# Format code with black
black .

# Fix common issues with autopep8
autopep8 --in-place --recursive .

# Or use ruff (modern, fast)
ruff check --fix .
```

---

## Basic API Tests

The CI pipeline validates the `/version` endpoint response against the
`VERSION` constant in `version.py`. The expected value is derived directly
from that constant for the current build. If the endpoint returns a different
value, the CI job fails.
