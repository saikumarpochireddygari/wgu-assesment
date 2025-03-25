#!/usr/bin/env python3
"""
job_creator.py

This module provides the DatabricksJobCreator class, which serves two primary purposes:
  1. Ensure that a Databricks Repo exists for a given environment (dev, stage, or prod). If the repo
     already exists, it will be force-updated (i.e. updated to the specified branch) so that the latest
     changes from the GitHub repository are pulled.
  2. Deploy environment-specific jobs to Databricks using the new Databricks CLI command:
     "databricks bundle deploy". The bundle configuration is stored in an environment-specific folder
     (e.g. cli_tool/databricks_bundle_config/dev/bundle.yaml).

Usage:
    Instantiate the DatabricksJobCreator with the path to the bundle configuration file and the
    target environment. Then call the deploy_jobs() method to perform the following steps:
      - Verify (or create/update) the Databricks Repo.
      - Change into the directory containing the bundle.yaml.
      - Execute "databricks bundle deploy" to deploy the defined jobs.

Environment Variables:
    DATABRICKS_HOST  - The host URL for the Databricks workspace.
    DATABRICKS_TOKEN - The personal access token for authenticating with the Databricks REST API.

Example:
    python -m cli_tool.main deploy --env dev

For further details, please refer to the project documentation at README.MD.
"""

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

    # Environment-specific information for the Databricks Repos.
    # Each environment (dev, stage, prod) must have its own Databricks Repo path.
    # GitHub repository URL, provider, and target branch.
    # In my Case, I want my main branch code to be deployed/Checked across various repos paths of DBCks Workspace.
    ENV_REPO_INFO = {
        "dev": {
            "path": "/Repos/pochireddygari@gmail.com/wgu-assesment-dev",
            "url": "https://github.com/saikumarpochireddygari/wgu-assesment.git",
            "provider": "gitHub",
            "branch": "main",
        },
        "stage": {
            "path": "/Repos/pochireddygari@gmail.com/wgu-assesment-stage",
            "url": "https://github.com/saikumarpochireddygari/wgu-assesment.git",
            "provider": "gitHub",
            "branch": "main",
        },
        "prod": {
            "path": "/Repos/pochireddygari@gmail.com/wgu-assesment-prod",
            "url": "https://github.com/saikumarpochireddygari/wgu-assesment.git",
            "provider": "gitHub",
            "branch": "main",
        },
    }

    # Mapping for the location of the environment-specific bundle configuration files.
    ENV_BUNDLE_SUBFOLDER = {
        "dev": "cli_tool/databricks_bundle_config/dev",
        "stage": "cli_tool/databricks_bundle_config/stage",
        "prod": "cli_tool/databricks_bundle_config/prod",
    }

    def __init__(self, bundle_config_path: str, environment: str):
        """
        Initializes the DatabricksJobCreator.

        Parameters:
            bundle_config_path (str): Path to the environment-specific bundle.yaml configuration file.
            environment (str): The target environment (dev, stage, or prod).
        """

        self.bundle_config_path = bundle_config_path
        self.environment = environment

    def update_repo(self, host: str, token: str, repo_id: int, branch: str):
        """
        Force-update the existing Databricks Repo to the specified branch.

        This method sends a PATCH request to the Databricks Repos API so that the workspace repo is updated
        to the latest state from the remote GitHub repo.

        Parameters:
            host (str): Databricks host URL.
            token (str): Databricks personal access token.
            repo_id (int): ID of the existing repo in Databricks.
            branch (str): The branch to update to.
        """

        update_url = f"{host}/api/2.0/repos/{repo_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {"branch": branch}

        resp = requests.patch(update_url, headers=headers, json=payload)
        resp.raise_for_status()
        print(
            f"[{self.environment.upper()}] Repo ID {repo_id} updated to branch '{branch}'."
        )

    def create_repo_if_not_exists(self):
        """
        Creates or force-updates the Databricks Repo for the given environment.

        This method first checks if a repo exists at the specified path in the Databricks workspace.
        If it exists, it calls update_repo() to update it to the desired branch.
        Otherwise, it sends a POST request to create the repo.
        """

        if self.environment not in self.ENV_REPO_INFO:
            raise ValueError(
                f"Environment {self.environment} not found in ENV_REPO_INFO."
            )

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
            "Content-Type": "application/json",
        }

        # Check if the Repo path already exists
        path_prefix = urllib.parse.quote(repo_path, safe="")
        check_url = f"{host}/api/2.0/repos?path_prefix={path_prefix}"
        resp = requests.get(check_url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        found_repo = None
        # Look through returned repos to see if one matches our target path.
        for r in data.get("repos", []):
            if r.get("path") == repo_path:
                found_repo = r
                break

        if found_repo:
            # If the repo exists, update it to the desired branch.
            print(
                f"[{self.environment.upper()}] Repo '{repo_path}' already exists. Updating to branch '{branch}'..."
            )
            self.update_repo(host, token, found_repo["id"], branch)
        else:
            # If the repo does not exist, create it.
            print(
                f"[{self.environment.upper()}] Repo '{repo_path}' not found. Creating new repo..."
            )
            create_payload = {
                "url": repo_url,
                "provider": provider,
                "path": repo_path,
                "branch": branch,
            }
            create_url = f"{host}/api/2.0/repos"
            create_resp = requests.post(
                create_url, headers=headers, json=create_payload
            )
            print("Databricks Repos API response:", create_resp.text)
            create_resp.raise_for_status()
            created_repo = create_resp.json()
            print(
                f"[{self.environment.upper()}] Created repo at path: {created_repo.get('path')}"
            )

    def deploy_jobs(self, max_retries=3):
        """
        Deploys Databricks jobs using the 'databricks bundle deploy' command.

        This method:
          1. Ensures the Databricks Repo is created or updated.
          2. Changes the working directory to the folder containing the bundle.yaml.
          3. Executes 'databricks bundle deploy' to deploy jobs as defined in the configuration.
          4. Retries deployment up to max_retries if failures occur.
          5. Restores the original working directory regardless of success or failure.
        """

        # First create or update the repo
        self.create_repo_if_not_exists()

        # Looking up the subfolder where the environment bundle.yaml resides.
        subfolder = self.ENV_BUNDLE_SUBFOLDER[self.environment]
        original_dir = os.getcwd()

        try:
            os.chdir(subfolder)  # Change directory to where bundle.yaml is located
            command = ["databricks", "bundle", "deploy"]
            print(
                f"[{self.environment.upper()}] Running: {' '.join(command)} in {subfolder}"
            )

            # Attempt to deploy the bundle with retries.
            for attempt in range(1, max_retries + 1):
                try:
                    subprocess.run(command, check=True)
                    print(
                        f"[{self.environment.upper()}] Successfully deployed Databricks Jobs."
                    )
                    return  # Exit on success
                except subprocess.CalledProcessError as e:
                    print(f"[{self.environment.upper()}] Attempt {attempt} failed: {e}")
                    if attempt < max_retries:
                        time.sleep(5)  # Wait before retrying
                    else:
                        raise RuntimeError(
                            f"[{self.environment.upper()}] Failed to deploy after {max_retries} attempts."
                        ) from e
        finally:
            os.chdir(original_dir)  # Always revert back to the original directory
