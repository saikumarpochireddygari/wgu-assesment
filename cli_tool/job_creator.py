import subprocess
import time
import os
import requests
import urllib.parse

class DatabricksJobCreator:
    """
    OOP class to:
      1. Ensure a Databricks Repo is created or updated for a given environment.
      2. Deploy environment-specific jobs using the new Databricks CLI 'databricks bundle deploy'.
    """

    ENV_REPO_INFO = {
        "dev": {
            # Path in Databricks workspace
            "path": "/Repos/pochireddygari@gmail.com/wgu-assesment-dev",
            # GitHub info
            "url": "https://github.com/saikumarpochireddygari/wgu-assesment.git",
            "provider": "gitHub",
            "branch": "main"
        },
        "stage": {
            "path": "/Repos/pochireddygari@gmail.com/wgu-assesment-stage",
            "url": "https://github.com/saikumarpochireddygari/wgu-assesment.git",
            "provider": "gitHub",
            "branch": "main"
        },
        "prod": {
            "path": "/Repos/pochireddygari@gmail.com/wgu-assesment-prod",
            "url": "https://github.com/saikumarpochireddygari/wgu-assesment.git",
            "provider": "gitHub",
            "branch": "main"
        },
    }

    # The subfolder with the environment's bundle.yaml
    ENV_BUNDLE_SUBFOLDER = {
        "dev": "cli_tool/databricks_bundle_config/dev",
        "stage": "cli_tool/databricks_bundle_config/stage",
        "prod": "cli_tool/databricks_bundle_config/prod",
    }

    def __init__(self, bundle_config_path: str, environment: str):
        self.bundle_config_path = bundle_config_path
        self.environment = environment

    def update_repo(self, host: str, token: str, repo_id: int, branch: str):
        """
        Force-update the existing repo to the given branch,
        pulling latest changes from remote.
        """
        update_url = f"{host}/api/2.0/repos/{repo_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"branch": branch}

        resp = requests.patch(update_url, headers=headers, json=payload)
        resp.raise_for_status()
        print(f"[{self.environment.upper()}] Repo ID {repo_id} updated to branch '{branch}'.")

    def create_repo_if_not_exists(self):
        """Create or force-update the environment's Databricks Repo."""
        if self.environment not in self.ENV_REPO_INFO:
            raise ValueError(f"Environment {self.environment} not found in ENV_REPO_INFO.")

        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")
        if not host or not token:
            raise ValueError("DATABRICKS_HOST or DATABRICKS_TOKEN not set.")

        host = host.rstrip("/")  # remove trailing slash

        repo_info = self.ENV_REPO_INFO[self.environment]
        repo_path = repo_info["path"]
        repo_url = repo_info["url"]
        provider = repo_info["provider"]
        branch = repo_info.get("branch", "main")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 1) Check if the Repo path already exists
        path_prefix = urllib.parse.quote(repo_path, safe='')
        check_url = f"{host}/api/2.0/repos?path_prefix={path_prefix}"
        resp = requests.get(check_url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        found_repo = None
        for r in data.get("repos", []):
            if r.get("path") == repo_path:
                found_repo = r
                break

        if found_repo:
            # Force-update the existing repo
            print(f"[{self.environment.upper()}] Repo '{repo_path}' already exists. Updating to branch '{branch}'...")
            self.update_repo(host, token, found_repo["id"], branch)
        else:
            # Create it if not found
            print(f"[{self.environment.upper()}] Repo '{repo_path}' not found. Creating new repo...")
            create_payload = {
                "url": repo_url,
                "provider": provider,
                "path": repo_path,
                "branch": branch
            }
            create_url = f"{host}/api/2.0/repos"
            create_resp = requests.post(create_url, headers=headers, json=create_payload)
            print("Databricks Repos API response:", create_resp.text)
            create_resp.raise_for_status()
            created_repo = create_resp.json()
            print(f"[{self.environment.upper()}] Created repo at path: {created_repo.get('path')}")

    def deploy_jobs(self, max_retries=3):
        """Runs 'databricks bundle deploy' in the environment subfolder."""
        # First create or update the repo
        self.create_repo_if_not_exists()

        subfolder = self.ENV_BUNDLE_SUBFOLDER[self.environment]
        original_dir = os.getcwd()

        try:
            os.chdir(subfolder)  # cd to folder with bundle.yaml
            command = ["databricks", "bundle", "deploy"]
            print(f"[{self.environment.upper()}] Running: {' '.join(command)} in {subfolder}")

            for attempt in range(1, max_retries + 1):
                try:
                    subprocess.run(command, check=True)
                    print(f"[{self.environment.upper()}] Successfully deployed Databricks Jobs.")
                    return
                except subprocess.CalledProcessError as e:
                    print(f"[{self.environment.upper()}] Attempt {attempt} failed: {e}")
                    if attempt < max_retries:
                        time.sleep(5)
                    else:
                        raise RuntimeError(
                            f"[{self.environment.upper()}] Failed to deploy after {max_retries} attempts."
                        ) from e
        finally:
            os.chdir(original_dir)
