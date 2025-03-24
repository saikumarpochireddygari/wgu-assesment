# cli_tool/main.py

import argparse
import os
from cli_tool.job_creator import DatabricksJobCreator

def main():
    parser = argparse.ArgumentParser(description="CLI tool to deploy Databricks MLOps Jobs.")
    subparsers = parser.add_subparsers(dest="command")

    deploy_parser = subparsers.add_parser("deploy", help="Deploy environment-specific jobs.")
    deploy_parser.add_argument("--env", required=True, choices=["dev", "stage", "prod"],
                               help="Environment to deploy: dev, stage, or prod.")

    args = parser.parse_args()

    if args.command == "deploy":
        base_dir = os.path.dirname(os.path.abspath(__file__))  # e.g. /path/to/cli_tool
        config_path = os.path.join(base_dir, "databricks_bundle_config", args.env, "bundle.yaml")

        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"No bundle.yaml found at: {config_path}")

        job_creator = DatabricksJobCreator(bundle_config_path=config_path, environment=args.env)
        job_creator.deploy_jobs()

if __name__ == "__main__":
    main()
