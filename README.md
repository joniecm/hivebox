[![Dynamic DevOps Roadmap](https://img.shields.io/badge/Dynamic_DevOps_Roadmap-559e11?style=for-the-badge&logo=Vercel&logoColor=white)](https://devopsroadmap.io/getting-started/)
[![Community](https://img.shields.io/badge/Join_Community-%23FF6719?style=for-the-badge&logo=substack&logoColor=white)](https://newsletter.devopsroadmap.io/subscribe)
[![Telegram Group](https://img.shields.io/badge/Telegram_Group-%232ca5e0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/DevOpsHive/985)
[![Fork on GitHub](https://img.shields.io/badge/Fork_On_GitHub-%2336465D?style=for-the-badge&logo=github&logoColor=white)](https://github.com/DevOpsHiveHQ/devops-hands-on-project-hivebox/fork)

# HiveBox - DevOps End-to-End Hands-On Project

<p align="center">
  <a href="https://devopsroadmap.io/projects/hivebox" style="display: block; padding: .5em 0; text-align: center;">
    <img alt="HiveBox - DevOps End-to-End Hands-On Project" border="0" width="90%" src="https://devopsroadmap.io/img/projects/hivebox-devops-end-to-end-project.png" />
  </a>
</p>

> [!CAUTION] > **[Fork](https://github.com/DevOpsHiveHQ/devops-hands-on-project-hivebox/fork)** this repo, and create PRs in your fork, **NOT** in this repo!

> [!TIP]
> If you are looking for the full roadmap, including this project, go back to the [getting started](https://devopsroadmap.io/getting-started) page.

This repository is the starting point for [HiveBox](https://devopsroadmap.io/projects/hivebox/), the end-to-end hands-on project.

You can fork this repository and start implementing the [HiveBox](https://devopsroadmap.io/projects/hivebox/) project. HiveBox project follows the same Dynamic MVP-style mindset used in the [roadmap](https://devopsroadmap.io/).

The project aims to cover the whole Software Development Life Cycle (SDLC). That means each phase will cover all aspects of DevOps, such as planning, coding, containers, testing, continuous integration, continuous delivery, infrastructure, etc.

Happy DevOpsing ♾️

## Before you start

Here is a pre-start checklist:

- ⭐ <a target="_blank" href="https://github.com/DevOpsHiveHQ/dynamic-devops-roadmap">Star the **roadmap** repo</a> on GitHub for better visibility.
- ✉️ <a target="_blank" href="https://newsletter.devopsroadmap.io/subscribe">Join the community</a> for the project community activities, which include mentorship, job posting, online meetings, workshops, career tips and tricks, and more.
- 🌐 <a target="_blank" href="https://t.me/DevOpsHive/985">Join the Telegram group</a> for interactive communication.

## Preparation

- [Create GitHub account](https://docs.github.com/en/get-started/start-your-journey/creating-an-account-on-github) (if you don't have one), then [fork this repository](https://github.com/DevOpsHiveHQ/devops-hands-on-project-hivebox/fork) and start from there.
- [Create GitHub project board](https://docs.github.com/en/issues/planning-and-tracking-with-projects/creating-projects/creating-a-project) for this repository (use `Kanban` template).
- Each phase should be presented as a pull request against the `main` branch. Don’t push directly to the main branch!
- Document as you go. Always assume that someone else will read your project at any phase.
- You can get senseBox IDs by checking the [openSenseMap](https://opensensemap.org/) website. Use 3 senseBox IDs close to each other (you can use the following [5eba5fbad46fb8001b799786](https://opensensemap.org/explore/5eba5fbad46fb8001b799786), [5c21ff8f919bf8001adf2488](https://opensensemap.org/explore/5c21ff8f919bf8001adf2488), and [5ade1acf223bd80019a1011c](https://opensensemap.org/explore/5ade1acf223bd80019a1011c)). Just copy the IDs, you will need them in the next steps.

<br/>
<p align="center">
  <a href="https://devopsroadmap.io/projects/hivebox/" imageanchor="1">
    <img src="https://img.shields.io/badge/Get_Started_Now-559e11?style=for-the-badge&logo=Vercel&logoColor=white" />
  </a><br/>
</p>

---

## Implementation

### Versioning

This project follows Semantic Versioning 2.0.0 (https://semver.org).

- Version numbers are stored in `version.py`
- Releases are tagged as `vMAJOR.MINOR.PATCH`
- Breaking changes increment MAJOR
- New features increment MINOR
- Bug fixes increment PATCH

### API Endpoints

#### GET /version

Returns the version of the currently deployed application.

**Parameters:** None

**Response:**

```json
{
  "version": "v0.0.1"
}
```

**Example:**

```bash
curl http://localhost:5000/version
```

#### GET /temperature

Returns the current average temperature across all configured senseBoxes.

**Parameters:** None

**Response (Success):**

```json
{
  "average_temperature": 22.46
}
```

**Response (Error - No Data Available):**

```json
{
  "error": "No temperature data available",
  "message": "Unable to retrieve fresh temperature data from senseBoxes. Data may be unavailable or older than 1 hour."
}
```

**Status Codes:**

- `200 OK`: Temperature data retrieved successfully
- `503 Service Unavailable`: No fresh temperature data available

**Notes:**

- Only includes temperature data from the last hour
- Temperature is rounded to 2 decimal places
- Fetches data from openSenseMap API (https://api.opensensemap.org)
- Configured senseBox IDs are stored in `sensebox_service.py`

**Example:**

```bash
curl http://localhost:5000/temperature
```

### How to run locally

#### Install dependencies

```bash
pip install -r requirements.txt
```

#### Run as web server

Run the Flask web application:

```bash
python app.py
```

The server will start on `http://0.0.0.0:5000`. You can then access the `/version` endpoint:

```bash
curl http://localhost:5000/version
```

#### Run as CLI (print version)

To print the version and exit:

```bash
python app.py --version
```

#### Run tests

```bash
python -m unittest test_app.py -v
```

### Code Quality & Linting

This project uses automated linting tools to maintain code quality and consistency.

#### Python Linting with flake8

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

### How to run using Docker

This repository includes a `Dockerfile` that runs the Flask web application.

Build the image:

```
docker build -t hivebox:latest .
```

Run the container:

```
docker run --rm -p 5000:5000 hivebox:latest
```

Then access the version endpoint:

```bash
curl http://localhost:5000/version
```
