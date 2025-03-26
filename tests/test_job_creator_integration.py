#!/usr/bin/env python3
"""
Integration tests for DatabricksJobCreator.

This integration test:
  1. Uses actual Databricks credentials from environment variables.
  2. Instantiates the DatabricksJobCreator for a test environment (e.g. "test").
  3. Calls deploy_jobs() to create (or update) the Databricks Repo and deploy jobs.
  4. Verifies that the repo exists via the Databricks Repos API.
  5. Cleans up by deleting the created repo and the deployed jobs.

Note:
  - This test interacts with the actual Databricks REST API.
  - Ensure that DATABRICKS_HOST and DATABRICKS_TOKEN are set to valid test values.
  - Adjust job name filters as needed for your bundle configuration.
"""

import os
import unittest
import requests
from urllib.parse import quote

from cli_tool.job_creator import DatabricksJobCreator


class TestJobCreatorIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Retrieving credentials from environment variables.
        cls.host = os.getenv("DATABRICKS_HOST")
        cls.token = os.getenv("DATABRICKS_TOKEN")
        if not cls.host or not cls.token:
            raise Exception(
                "DATABRICKS_HOST and DATABRICKS_TOKEN must be set for integration tests."
            )
        cls.host = cls.host.rstrip("/")
        cls.headers = {
            "Authorization": f"Bearer {cls.token}",
            "Content-Type": "application/json",
        }
        # Using a dedicated test environment
        cls.env = "test"
        # Fetching path
        cls.repo_path = DatabricksJobCreator.ENV_REPO_INFO[cls.env]["path"]

    def test_create_update_and_cleanup_repo_and_jobs(self):
        """
        This test:
          1. Deploys jobs using deploy_jobs(), which creates or updates the repo.
          2. Verifies the repo exists via the Databricks Repos API.
          3. Deletes the created repo.
          4. Lists jobs and deletes any jobs created as part of the bundle deployment.
        """
        bundle_config_path = "cli_tool/databricks_bundle_config/test/bundle.yaml"
        creator = DatabricksJobCreator(bundle_config_path, "test")

        # Deploying job (this will create/update the repo and attempt to deploy jobs)
        creator.deploy_jobs(max_retries=1)

        # Verifying the repo exists using the Databricks Repos API.
        path_prefix = quote(self.repo_path, safe="")
        get_url = f"{self.host}/api/2.0/repos?path_prefix={path_prefix}"
        resp = requests.get(get_url, headers=self.headers)
        self.assertEqual(
            resp.status_code, 200, "Expected a 200 OK from the repos GET request."
        )
        data = resp.json()
        repo_found = None
        for r in data.get("repos", []):
            if r.get("path") == self.repo_path:
                repo_found = r
                break
        self.assertIsNotNone(repo_found, "Test repo should exist after deployment.")

        # Deleting the created repo.
        repo_id = repo_found.get("id")
        self.assertIsNotNone(repo_id, "Repo ID should be available for cleanup.")
        delete_url = f"{self.host}/api/2.0/repos/{repo_id}"
        del_resp = requests.delete(delete_url, headers=self.headers)
        self.assertEqual(
            del_resp.status_code,
            200,
            "Expected a 200 OK response when deleting the repo.",
        )
        print("Cleanup: Repo deleted successfully.")

        # Listing all jobs using the Jobs API
        jobs_url = f"{self.host}/api/2.1/jobs/list"
        jobs_resp = requests.get(jobs_url, headers=self.headers)
        self.assertEqual(
            jobs_resp.status_code, 200, "Expected a 200 OK from the jobs list API."
        )
        jobs_data = jobs_resp.json()

        jobs_to_delete = ["my_training_job_test"]
        deleted_jobs = []

        # deleting the test job
        for job in jobs_data.get("jobs", []):
            job_name = job.get("settings", {}).get("name", "")
            if job_name in jobs_to_delete:
                job_id = job.get("job_id")
                self.assertIsNotNone(
                    job_id, f"Job ID for {job_name} should be available for cleanup."
                )
                delete_payload = {"job_id": job_id}
                delete_job_url = f"{self.host}/api/2.1/jobs/delete"
                del_job_resp = requests.post(
                    delete_job_url, headers=self.headers, json=delete_payload
                )
                self.assertEqual(
                    del_job_resp.status_code,
                    200,
                    f"Expected a 200 OK response when deleting job {job_name}.",
                )
                deleted_jobs.append(job_name)
        print("Cleanup: Deleted jobs:", deleted_jobs)


if __name__ == "__main__":
    unittest.main()
