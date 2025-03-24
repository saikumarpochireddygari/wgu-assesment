# tests/test_job_creator.py

import unittest
from unittest.mock import patch, MagicMock
import os

from cli_tool.job_creator import DatabricksJobCreator

class TestDatabricksJobCreator(unittest.TestCase):

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://test.cloud.databricks.com", 
                             "DATABRICKS_TOKEN": "test-token"})
    @patch("cli_tool.job_creator.requests.get")
    @patch("cli_tool.job_creator.requests.post")
    @patch("cli_tool.job_creator.subprocess.run")
    def test_deploy_jobs_dev(self, mock_subprocess, mock_post, mock_get):
        # Mock: no repos found
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"repos": []})
        # Mock: successful creation
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"path": "/Repos/test-created"})

        bundle_config_path = "cli_tool/databricks_bundle_config/dev/bundle.yaml"
        job_creator = DatabricksJobCreator(bundle_config_path, "dev")

        # Act
        job_creator.deploy_jobs(max_retries=1)

        # Assert
        mock_get.assert_called_once()
        mock_post.assert_called_once()
        mock_subprocess.assert_called_once()

if __name__ == "__main__":
    unittest.main()
