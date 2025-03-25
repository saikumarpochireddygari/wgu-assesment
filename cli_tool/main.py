#!/usr/bin/env python3
"""
main.py - ML Deployment CLI for Databricks Jobs

This script is the entry point for deploying environment-specific Databricks jobs
as part of our MLOps pipeline. It plugs together various components and configurations,
performing the following tasks:

  1. Parses command-line arguments using argparse.
  2. Determines the target environment (dev, stage, or prod).
  3. Constructs the path to the appropriate Databricks bundle configuration file (bundle.yaml)
     located in the "cli_tool/databricks_bundle_config/<env>/" directory.
  4. Instantiates the DatabricksJobCreator class and triggers the deployment of jobs via the 
     Databricks CLI.

Usage:
    python -m cli_tool.main deploy --env <environment>

Where <environment> must be one of:
    - dev
    - stage
    - prod

Example:
    To deploy jobs for the development environment, run:
    
        python -m cli_tool.main deploy --env dev

Requirements:
    - Each environment must have a corresponding configuration file at:
      cli_tool/databricks_bundle_config/<env>/bundle.yaml
    - The DatabricksJobCreator class (in job_creator.py) handles:
          • Creating (or updating) the required Databricks Repo.
          • Changing directory to the environment-specific bundle config folder.
          • Executing the 'databricks bundle deploy' command to deploy/update jobs.
          
For more details, refer to the project documentation Readme.MD file.

"""

# Importing Packages
import argparse
import os
from cli_tool.job_creator import DatabricksJobCreator

def main():
    parser = argparse.ArgumentParser(description="CLI tool to deploy Databricks Jobs.")
    subparsers = parser.add_subparsers(dest="command")

    deploy_parser = subparsers.add_parser("deploy", help="Deploy environment-specific jobs.")
    deploy_parser.add_argument("--env", required=True, choices=["dev", "stage", "prod"],
                               help="Environment to deploy: dev, stage, or prod.")

    args = parser.parse_args()

    if args.command == "deploy":
        # this is /path/to/cli_tool, If user chooses to deploy, we first figure our out cli path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # As per Env provided in the CLI command, We check for env specific .yaml config in our "base_dir/databricks_bundle_config/env/" Folder
        config_path = os.path.join(base_dir, "databricks_bundle_config", args.env, "bundle.yaml")
        # if there is no file, we Raise an error
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"No bundle.yaml found at: {config_path}")

        # Next we instantiate a Databricks Job Creator Class by passing in Args and calling deploy_jobs method.
        job_creator = DatabricksJobCreator(bundle_config_path=config_path, environment=args.env)
        job_creator.deploy_jobs()

if __name__ == "__main__":
    main()
