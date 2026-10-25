import os
import sys
import gc
import re
import site
import base64
import shutil

def hack_mlflow_ui():
    """Injects custom NRS MLOps branding (logo, favicon, app name, #D42e12 & #7D858b colors) into MLflow UI static build."""
    print("Step 1: Injecting NRS MLOps corporate branding into MLflow UI assets...", flush=True)

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

    # Read the attached NRS logo
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, 'assets', 'nrs_logo.png')
    logo_data_uri = None
    logo_bytes = None

    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            logo_bytes = f.read()
        b64_logo = base64.b64encode(logo_bytes).decode('ascii')
        logo_data_uri = f"data:image/png;base64,{b64_logo}"
        print(f"Loaded NRS logo asset ({len(logo_bytes)} bytes).", flush=True)

    # 1. Patch index.html (Title, Favicon, Theme Color)
    index_html_path = os.path.join(mlflow_path, 'index.html')
    if os.path.exists(index_html_path):
        try:
            with open(index_html_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Change App Title to "NRS MLOps"
            content = re.sub(r'<title>[^<]*</title>', '<title>NRS MLOps</title>', content)

            # Update Favicon to NRS logo
            if logo_data_uri:
                favicon_tags = (
                    f'<link rel="shortcut icon" href="{logo_data_uri}"/>\n'
                    f'<link rel="icon" type="image/png" href="{logo_data_uri}"/>'
                )
                if '<link rel="shortcut icon"' in content:
                    content = re.sub(r'<link rel="shortcut icon"[^>]*>', favicon_tags, content)
                elif '<link rel="icon"' in content:
                    content = re.sub(r'<link rel="icon"[^>]*>', favicon_tags, content)

            # Update meta theme-color to #D42e12
            content = re.sub(r'<meta name="theme-color" content="[^"]*"/>', '<meta name="theme-color" content="#D42e12"/>', content)

            with open(index_html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Patched index.html with 'NRS MLOps' title and logo favicon.", flush=True)
        except Exception as e:
            print(f"Warning: Could not patch index.html: {e}", flush=True)

    # 2. Overwrite favicon.ico with NRS logo
    if logo_bytes:
        try:
            fav_path = os.path.join(mlflow_path, 'favicon.ico')
            with open(fav_path, 'wb') as f:
                f.write(logo_bytes)
            print("Overwrote favicon.ico with NRS logo.", flush=True)
        except Exception as e:
            print(f"Warning: Could not overwrite favicon.ico: {e}", flush=True)

    # 3. Overwrite MLflow logo files in static/media/
    media_dir = os.path.join(mlflow_path, 'static', 'media')
    if os.path.exists(media_dir) and logo_bytes:
        try:
            for fname in os.listdir(media_dir):
                if 'home-logo' in fname or 'logo' in fname:
                    target = os.path.join(media_dir, fname)
                    with open(target, 'wb') as f:
                        f.write(logo_bytes)
                    print(f"Replaced media asset '{fname}' with NRS logo.", flush=True)

            # Also ensure a static nrs_logo.png is in static/ and static/media/
            with open(os.path.join(media_dir, 'nrs_logo.png'), 'wb') as f:
                f.write(logo_bytes)
            with open(os.path.join(mlflow_path, 'static', 'nrs_logo.png'), 'wb') as f:
                f.write(logo_bytes)
        except Exception as e:
            print(f"Warning: Could not update media assets: {e}", flush=True)

    # 4. Patch JS bundles (App Name in Header, Color Overrides)
    js_dir = os.path.join(mlflow_path, 'static', 'js')
    if os.path.exists(js_dir):
        for fname in os.listdir(js_dir):
            if fname.endswith('.js'):
                js_file = os.path.join(js_dir, fname)
                try:
                    with open(js_file, 'r', encoding='utf-8') as f:
                        js_code = f.read()

                    modified = False
                    if 'alt:"MLflow"' in js_code:
                        js_code = js_code.replace('alt:"MLflow"', 'alt:"NRS MLOps"')
                        modified = True

                    # Header background: #0b3574 -> #1c2125
                    if '#0b3574' in js_code:
                        js_code = js_code.replace('#0b3574', '#1c2125')
                        modified = True

                    # Header active nav border: #43C9ED -> #D42e12
                    if '#43C9ED' in js_code:
                        js_code = js_code.replace('#43C9ED', '#D42e12')
                        modified = True

                    # Primary blue: #2272b4 -> #D42e12
                    if '#2272b4' in js_code:
                        js_code = js_code.replace('#2272b4', '#D42e12')
                        modified = True

                    if modified:
                        with open(js_file, 'w', encoding='utf-8') as f:
                            f.write(js_code)
                        print(f"Patched JS bundle {fname} with NRS branding.", flush=True)
                except Exception as e:
                    print(f"Warning: Could not patch JS bundle {fname}: {e}", flush=True)

    # 5. Patch CSS stylesheets (Primary #D42e12, Secondary #7D858b)
    css_branding = """
/* ==================== NRS MLOps Corporate Branding ==================== */
:root {
  --nrs-primary: #D42e12 !important;
  --nrs-primary-hover: #b0240d !important;
  --nrs-primary-active: #941e0a !important;
  --nrs-primary-light: #fdf1ef !important;
  --nrs-secondary: #7D858b !important;
  --nrs-secondary-hover: #656c71 !important;
  --nrs-secondary-light: #f4f5f6 !important;
}

/* Header styling */
header {
  background-color: #1c2125 !important;
  border-bottom: 2px solid #D42e12 !important;
}
header a {
  color: #e7f1fb !important;
  transition: color 0.15s ease-in-out !important;
}
header a:hover {
  color: #D42e12 !important;
}

/* Logo display in header & all instances */
header img, .navbar-brand img, img[alt*="NRS"], img[alt="MLflow"], img[src*="home-logo"] {
  height: 38px !important;
  max-height: 38px !important;
  width: auto !important;
  object-fit: contain !important;
  background: rgba(255, 255, 255, 0.95) !important;
  padding: 3px 8px !important;
  border-radius: 6px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25) !important;
}

/* Primary Buttons (#D42e12) */
.ant-btn-primary, button[type="primary"], .btn-primary, [class*="Button-primary"] {
  background-color: #D42e12 !important;
  border-color: #D42e12 !important;
  color: #ffffff !important;
}
.ant-btn-primary:hover, .ant-btn-primary:focus, button[type="primary"]:hover, .btn-primary:hover {
  background-color: #b0240d !important;
  border-color: #b0240d !important;
  color: #ffffff !important;
}

/* Secondary Buttons & Accents (#7D858b) */
.ant-btn-default, button.secondary, .btn-secondary, [class*="Button-secondary"] {
  border-color: #7D858b !important;
  color: #333b40 !important;
}
.ant-btn-default:hover, button.secondary:hover {
  border-color: #D42e12 !important;
  color: #D42e12 !important;
}

/* Links & Accents */
a, [class*="Link"] {
  color: #D42e12;
}
a:hover, [class*="Link"]:hover {
  color: #b0240d;
}

/* Tabs Navigation */
.ant-tabs-ink-bar {
  background-color: #D42e12 !important;
}
.ant-tabs-tab.ant-tabs-tab-active .ant-tabs-tab-btn {
  color: #D42e12 !important;
  font-weight: 600 !important;
}
.ant-tabs-tab:hover {
  color: #b0240d !important;
}

/* Pagination, Radios, Checkboxes, Switches */
.ant-pagination-item-active {
  border-color: #D42e12 !important;
}
.ant-pagination-item-active a {
  color: #D42e12 !important;
}
.ant-checkbox-checked .ant-checkbox-inner {
  background-color: #D42e12 !important;
  border-color: #D42e12 !important;
}
.ant-radio-checked .ant-radio-inner {
  border-color: #D42e12 !important;
}
.ant-radio-checked .ant-radio-inner::after {
  background-color: #D42e12 !important;
}
.ant-switch-checked {
  background-color: #D42e12 !important;
}

/* Tags, Badges & Table Headers */
.ant-tag-blue, .ant-tag-has-color {
  background-color: #fdf1ef !important;
  border-color: #7D858b !important;
  color: #D42e12 !important;
}
.ant-badge-count {
  background-color: #D42e12 !important;
}
.ant-table-thead > tr > th {
  border-bottom: 2px solid #7D858b !important;
}
"""

    css_dir = os.path.join(mlflow_path, 'static', 'css')
    if os.path.exists(css_dir):
        color_replacements = [
            ('#2272b4', '#D42e12'),
            ('#1d517c', '#b0240d'),
            ('#3f81b1', '#e0462c'),
            ('#1890ff', '#D42e12'),
            ('#096dd9', '#b0240d'),
            ('#40a9ff', '#e0462c'),
            ('#43c9ed', '#D42e12'),
            ('#43C9ED', '#D42e12'),
            ('#0b3574', '#1c2125'),
        ]

        for fname in os.listdir(css_dir):
            if fname.endswith('.css'):
                css_file = os.path.join(css_dir, fname)
                try:
                    with open(css_file, 'r', encoding='utf-8') as f:
                        css_content = f.read()

                    # Apply theme color replacements
                    for old_col, new_col in color_replacements:
                        css_content = css_content.replace(old_col, new_col)

                    # Append custom branding CSS rules if not already present
                    if "/* ==================== NRS MLOps Corporate Branding ==================== */" not in css_content:
                        css_content += f"\n{css_branding}"

                    with open(css_file, 'w', encoding='utf-8') as f:
                        f.write(css_content)
                    print(f"Injected theme colors (#D42e12, #7D858b) into CSS: {fname}", flush=True)
                except Exception as e:
                    print(f"Warning: Could not patch CSS file {fname}: {e}", flush=True)

    print("All NRS MLOps branding layers applied successfully.", flush=True)


def seed_baseline_data(sqlite_uri):
    """Initializes SQLite schema and populates baseline NRS MLOps demo profiles directly."""
    print("Step 2: Checking and initializing baseline NRS SQLite database...", flush=True)
    try:
        import mlflow
        mlflow.set_tracking_uri(sqlite_uri)

        experiment_name = "NRS MLOps - Risk Scoring & Anomaly Detection"
        exp = mlflow.get_experiment_by_name(experiment_name)

        if exp is None:
            print(f"Fresh database detected. Initializing '{experiment_name}'...", flush=True)
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

            print(f"Successfully seeded '{experiment_name}'.", flush=True)
        else:
            print(f"NRS experiment '{experiment_name}' already present.", flush=True)
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