import os
import sys
import gc
import site

def hack_mlflow_ui():
    """Injects custom branding (titles, logo) into the MLflow UI static build."""
    print("Step 1: Injecting NRS corporate branding into MLflow UI layout...", flush=True)

    candidate_paths = []
    try:
        import mlflow
        candidate_paths.append(os.path.join(os.path.dirname(mlflow.__file__), 'server', 'js', 'build'))
    except Exception:
        pass

    try:
        if hasattr(site, 'getsitepackages'):
            for p in site.getsitepackages():
                candidate_paths.append(os.path.join(p, 'mlflow', 'server', 'js', 'build'))
        if hasattr(site, 'getusersitepackages'):
            candidate_paths.append(os.path.join(site.getusersitepackages(), 'mlflow', 'server', 'js', 'build'))
    except Exception:
        pass

    mlflow_path = None
    for path in candidate_paths:
        if os.path.exists(path):
            mlflow_path = path
            break

    if not mlflow_path:
        print("Warning: Could not locate MLflow asset build directory. Skipping UI modifications.", flush=True)
        return

    # Rewrite window and panel headers
    index_html_path = os.path.join(mlflow_path, 'index.html')
    if os.path.exists(index_html_path):
        try:
            with open(index_html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if "<title>MLflow</title>" in content:
                content = content.replace("<title>MLflow</title>", "<title>NRS ModelOps Platform</title>")
                with open(index_html_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("Applied NRS title to MLflow UI index.html.", flush=True)
        except Exception as e:
            print(f"Warning: Could not patch index.html: {e}", flush=True)

    # Configurable brand logo with high-resolution inline SVG fallback
    default_logo = (
        "data:image/svg+xml;utf8,"
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 48'>"
        "<rect width='200' height='48' rx='6' fill='%23005A36'/>"
        "<text x='16' y='32' font-family='sans-serif' font-size='20' font-weight='bold' fill='%23ffffff'>NRS</text>"
        "<text x='70' y='31' font-family='sans-serif' font-size='13' font-weight='600' fill='%23A3D9C9'>ModelOps</text>"
        "</svg>"
    )
    nrs_logo_url = os.environ.get("NRS_LOGO_URL", default_logo)

    branding_rule = (
        f"/* NRS Branding Injection */\n"
        f".navbar-brand {{ background-image: url('{nrs_logo_url}') !important; "
        f"background-size: contain !important; background-repeat: no-repeat !important; "
        f"width: 140px !important; }}\n"
    )

    main_css_dir = os.path.join(mlflow_path, 'static', 'css')
    if os.path.exists(main_css_dir):
        for file in os.listdir(main_css_dir):
            if file.endswith('.css'):
                css_file_path = os.path.join(main_css_dir, file)
                try:
                    with open(css_file_path, 'r', encoding='utf-8') as f:
                        css_content = f.read()
                    if "/* NRS Branding Injection */" not in css_content:
                        with open(css_file_path, 'a', encoding='utf-8') as f:
                            f.write(f"\n{branding_rule}")
                except Exception as e:
                    print(f"Warning: Could not patch CSS file {file}: {e}", flush=True)

    print("Branding layers loaded successfully.", flush=True)

def seed_baseline_data(sqlite_uri):
    """Initializes SQLite schema and populates baseline NRS demo profiles directly."""
    print("Step 2: Checking and initializing baseline NRS SQLite database...", flush=True)
    try:
        import mlflow
        mlflow.set_tracking_uri(sqlite_uri)

        experiment_name = "NRS Risk Scoring & Anomaly Detection"
        exp = mlflow.get_experiment_by_name(experiment_name)

        if exp is None:
            print("Fresh SQLite database detected. Populating mock NRS operational profiles...", flush=True)
            exp_id = mlflow.create_experiment(experiment_name)

            # --- PROFILE 1: Income Tax Fraud Risk Scorer ---
            with mlflow.start_run(experiment_id=exp_id, run_name="Income Tax Risk Scorer v2.1"):
                mlflow.set_tag("NRS-Governance", "Pending-Manager-Approval")
                mlflow.set_tag("ModelType", "XGBoost-Classifier")
                mlflow.set_tag("Data-Lineage", "NRS_Taxpayer_2026_Q3")

                for epoch in range(1, 25):
                    mlflow.log_metric("Model Accuracy", 0.75 + (0.13 * (1 - (1 / epoch))), step=epoch)
                    mlflow.log_metric("Silent Drift Error", 0.40 * (1 / epoch), step=epoch)

                mlflow.log_param("Risk Threshold Tier", "High-Certainty (>85%)")
                mlflow.log_param("Auditable Commits", "git-sha-nrs-9a2c4e")

            # --- PROFILE 2: VAT Anomaly Detector ---
            with mlflow.start_run(experiment_id=exp_id, run_name="VAT Corporate Anomaly Detector"):
                mlflow.set_tag("NRS-Governance", "Approved-In-Production")
                mlflow.set_tag("ModelType", "Isolation-Forest")
                mlflow.set_tag("Data-Lineage", "Corporate_Returns_2026_Final")

                for epoch in range(1, 20):
                    mlflow.log_metric("Model Accuracy", 0.80 + (0.11 * (1 - (1 / epoch))), step=epoch)
                    mlflow.log_metric("Silent Drift Error", 0.12 + (0.06 * (epoch / 20)), step=epoch)

                mlflow.log_param("Anomaly Sensitivity Rate", "0.02")

            print("Successfully initialized and seeded fresh SQLite database.", flush=True)
        else:
            print(f"NRS platform experiment '{experiment_name}' already present.", flush=True)
    except Exception as e:
        print(f"Warning: Direct database initialization encountered: {e}", flush=True)
    finally:
        # Reclaim memory before server launch
        gc.collect()

if __name__ == "__main__":
    port = os.environ.get("PORT", "10000")
    db_path = os.path.abspath("mlflow.db")
    sqlite_uri = f"sqlite:///{db_path}"

    os.makedirs("./mlruns", exist_ok=True)

    # 1. Inject corporate branding into UI files
    hack_mlflow_ui()

    # 2. Pre-seed SQLite database directly (zero network overhead, instant startup)
    seed_baseline_data(sqlite_uri)

    # 3. Clean up Python memory
    gc.collect()

    print(f"Step 3: Launching lightweight MLflow server on 0.0.0.0:{port} (single worker)...", flush=True)

    cmd = [
        sys.executable, "-m", "mlflow", "server",
        "--backend-store-uri", sqlite_uri,
        "--default-artifact-root", "./mlruns",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--workers", "1",
        "--serve-artifacts"
    ]

    # Use os.execvp to replace current process so MLflow becomes root process with zero wrapper overhead
    os.execvp(cmd[0], cmd)