import os
import sys
import time
import subprocess
import site
import threading

def hack_mlflow_ui():
    """Injects custom branding (titles, logo) into the MLflow UI static build."""
    print("Step 1: Injecting NRS corporate branding into MLflow UI layout...")

    # Locate MLflow UI static build assets across multiple candidate locations
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
        print("Warning: Could not locate asset build layout directory. Skipping UI modifications.")
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
                print("Applied NRS title to MLflow UI index.html.")
        except Exception as e:
            print(f"Warning: Could not patch index.html: {e}")

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
                    print(f"Warning: Could not patch CSS file {file}: {e}")

    print("Branding layers loaded successfully.")

def auto_seed_embedded_data(port):
    """Waits for local SQLite instance initialization, then builds custom NRS data structures."""
    import urllib.request
    import mlflow

    tracking_uri = f"http://127.0.0.1:{port}"
    print(f"Step 2: Polling MLflow server at {tracking_uri} before baseline data seeding...")
    mlflow.set_tracking_uri(tracking_uri)

    # Health check polling: wait up to 60 seconds for the MLflow server to be responsive
    server_ready = False
    for _ in range(30):
        try:
            req = urllib.request.Request(f"{tracking_uri}/health", headers={"User-Agent": "NRS-Seeder"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    server_ready = True
                    break
        except Exception:
            try:
                # Fallback to root path
                req = urllib.request.Request(tracking_uri, headers={"User-Agent": "NRS-Seeder"})
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status in (200, 301, 302):
                        server_ready = True
                        break
            except Exception:
                pass
        time.sleep(2)

    if not server_ready:
        print("Warning: MLflow server did not answer health check in time. Attempting seeding anyway...")

    try:
        experiment_name = "NRS Risk Scoring & Anomaly Detection"
        exp = mlflow.get_experiment_by_name(experiment_name)

        if exp is None:
            print("System booted fresh or wiped. Building mock NRS operational profiles...")
            exp_id = mlflow.create_experiment(experiment_name)
        else:
            exp_id = exp.experiment_id
            print(f"NRS platform experiment '{experiment_name}' found (ID: {exp_id}).")

        # Avoid creating duplicate runs on server reboots
        existing_runs = mlflow.search_runs(experiment_ids=[exp_id])
        if len(existing_runs) > 0:
            print(f"Experiment already populated with {len(existing_runs)} run(s). Skipping duplicate seed.")
            return

        print("Seeding baseline operational profiles...")
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

        print("Successfully seeded fresh embedded database data.")
    except Exception as e:
        print(f"Error executing database injection thread: {e}")

if __name__ == "__main__":
    hack_mlflow_ui()

    port = os.environ.get("PORT", "10000")
    db_path = os.path.abspath("mlflow.db")
    sqlite_uri = f"sqlite:///{db_path}"

    os.makedirs("./mlruns", exist_ok=True)

    print(f"Step 3: Launching standalone NRS ModelOps Platform on port {port}...")
    cmd = [
        sys.executable, "-m", "mlflow", "server",
        "--backend-store-uri", sqlite_uri,
        "--default-artifact-root", "./mlruns",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--serve-artifacts"
    ]

    try:
        process = subprocess.Popen(cmd)
    except FileNotFoundError:
        # Fallback to direct mlflow binary invocation
        cmd[0:3] = ["mlflow"]
        process = subprocess.Popen(cmd)

    # Fire the seeder loop asynchronously right after the server process begins spinup
    seeder_thread = threading.Thread(target=auto_seed_embedded_data, args=(port,))
    seeder_thread.daemon = True
    seeder_thread.start()

    # Keeps parent script active and gracefully handles shutdown signals
    try:
        process.wait()
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down NRS ModelOps Platform...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
