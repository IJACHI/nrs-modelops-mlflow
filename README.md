# NRS ModelOps Platform (MLflow)

Customized MLflow Tracking and ModelOps server tailored for NRS operational environments, supporting automated baseline dataset/metric seeding, corporate UI branding injection, and lightweight SQLite persistence.

---

## Features

- **Automated UI Branding**: Dynamically brands the MLflow web interface with NRS titles and corporate logos without needing to recompile the React frontend.
- **Auto-Seeding Baseline Data**: Automatically seeds baseline operational models, governance tags, and metrics (Income Tax Risk Scorer, VAT Corporate Anomaly Detector) on fresh deployments.
- **Zero-Configuration Deployment**: Runs as a self-contained web service ready for Render, Railway, Docker, or bare metal virtual machines.
- **Persistent SQLite & Artifact Storage**: Uses a local SQLite database (`mlflow.db`) and artifact directory (`./mlruns`).

---

## Repository Structure

```
├── app.py              # Main entrypoint: UI injection, seeding daemon, and MLflow server
├── requirements.txt    # MLflow and machine learning dependencies
├── Procfile            # Deployment process definition (Render / Heroku)
├── .gitignore          # Ignores runtime artifacts (mlflow.db, mlruns, pycache)
└── README.md           # Documentation
```

---

## Local Quickstart

### 1. Prerequisites
- Python 3.9 – 3.11 (e.g. `python3.10`). Python 3.13+ / 3.14+ is not recommended because MLflow and its C-extensions lack prebuilt wheels for pre-release Pythons.
- `pip`

### 2. Setup Virtual Environment

```bash
# Recommended: use Python 3.10
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Platform

```bash
python app.py
```

The MLflow dashboard will be accessible at `http://localhost:10000` (or the port defined by `PORT`).

---

## Configuration

The application can be configured via environment variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PORT` | `10000` | Port for the MLflow tracking web server. |
| `NRS_LOGO_URL` | Embedded SVG | Custom URL or Data URI for the navbar brand logo. |

---

## Deployment (Render / Cloud)

This repository includes [.python-version](file:///Users/ijachi/Documents/nrs-mlflow/.python-version) and [render.yaml](file:///Users/ijachi/Documents/nrs-mlflow/render.yaml) preconfigured for **Python 3.11.10** (ensuring all MLflow and PyArrow binary wheels install instantly without requiring CMake compilation).

1. Connect this GitHub repository (`IJACHI/nrs-modelops-mlflow`) to your Render account as a **Web Service**.
2. Render will automatically detect `.python-version` (or set Environment Variable `PYTHON_VERSION=3.11.10`).
3. Set the build and start commands in the Render Dashboard:

   **Build Command**:
   ```bash
   pip install -r requirements.txt
   ```

   **Start Command**:
   ```bash
   python app.py
   ```
4. Optionally attach a persistent disk mounted to `/app/mlruns` and store `mlflow.db` on persistent storage if run history persistence across redeploys is desired.
