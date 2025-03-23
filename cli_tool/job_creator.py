# cli_tool/job_creator.py

import subprocess
import time
import os
import requests
import urllib.parse

class DatabricksJobCreator:
    """
    OOP class to:
      1. Ensure a Databricks Repo is created at /Repos/... for a given environment.
      2. Deploy environment-specific jobs using Databricks Asset Bundles.
    """

    # ENV_REPO_INFO = {
    #     "dev": {
    #         "path": "/Repos/my-mlops-repo-dev",
    #         "url": "https://github.com/your-org/my-mlops-repo-dev.git",
    #         "provider": "gitHub"
    #     },
    #     "stage": {
    #         "path": "/Repos/my-mlops-repo-stage",
    #         "url": "https://github.com/your-org/my-mlops-repo-stage.git",
    #         "provider": "gitHub"
    #     },
    #     "prod": {
    #         "path": "/Repos/my-mlops-repo-prod",
    #         "url": "https://github.com/your-org/my-mlops-repo-prod.git",
    #         "provider": "gitHub"
    #     },
    # }
    ENV_REPO_INFO = {
        "dev": {
            "path": "/Repos/pochireddygari@gmail.com/wgu-assesment-dev",  
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


    def __init__(self, bundle_config_path: str, environment: str):
        """
        :param bundle_config_path: Path to the Databricks Asset Bundles YAML file.
        :param environment: 'dev', 'stage', or 'prod'
        """
        self.bundle_config_path = bundle_config_path
        self.environment = environment

    def create_repo_if_not_exists(self):
        """
        Calls Databricks Repos API to ensure the environment's
        Repo path is created. If it already exists, do nothing.
        """
        if self.environment not in self.ENV_REPO_INFO:
            raise ValueError(f"Environment {self.environment} not found in ENV_REPO_INFO.")

        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")
        if not host or not token:
            raise ValueError("DATABRICKS_HOST or DATABRICKS_TOKEN not set.")

        # remove trailing slash if present
        host = host.rstrip("/")

        repo_info = self.ENV_REPO_INFO[self.environment]
        repo_path = repo_info["path"]
        repo_url = repo_info["url"]
        provider = repo_info["provider"]

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

        for r in data.get("repos", []):
            if r.get("path") == repo_path:
                print(f"[{self.environment.upper()}] Repo path '{repo_path}' already exists.")
                return  # Found it, do nothing

        # 2) If not found, create it
        create_payload = {
            "url": repo_url,
            "provider": provider,
            "path": repo_path
        }
        create_url = f"{host}/api/2.0/repos"
        create_resp = requests.post(create_url, headers=headers, json=create_payload)
        print("Databricks Repos API response:", create_resp.text) 
        create_resp.raise_for_status()
        created_repo = create_resp.json()
        print(f"[{self.environment.upper()}] Created repo at path: {created_repo.get('path')}")

    def deploy_jobs(self, max_retries=3):
        """
        Ensures the Repo path is created, then deploys Databricks jobs
        using 'databricks bundles deploy'.
        """
        self.create_repo_if_not_exists()  # Make sure environment's Repo is present

        command = [
            "databricks",
            "bundles",
            "deploy",
            "--bundle-config",
            self.bundle_config_path
        ]

        print(f"[{self.environment.upper()}] Deploying jobs with: {' '.join(command)}")
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
