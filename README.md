# wgu-assesment

# MLOps on Databricks with Environment-Specific Deployments and CI/CD

This repository provides a comprehensive framework for managing machine learning operations (MLOps) on Databricks. It automates environment-specific job deployments via a Python CLI tool, integrates with MLflow for experiment tracking and model registry, Uses Unity Catalog for Data Governance. It also includes a robust CI/CD pipeline with unit/integration tests.

---

## Table of Contents

- [Overview](#overview)
- [Project Features](#project-features)
- [Repository Structure](#repository-structure)
- [Setup Instructions](#setup-instructions)
- [Usage Guide](#usage)
- [CLI Tool Overview](#cli-tool-overview)
- [Databricks Asset Bundles & Unity Catalog](#databricks-asset-bundles--unity-catalog)
- [MLflow Integration](#mlflow-integration)
- [Testing](#testing)
- [CI/CD Pipeline (GitHub Actions)](#cicd-pipeline-github-actions)
- [Keychanges Required](#Changes)
- [Contact](#contact)



---

## Overview

This project implements an end-to-end MLOps pipeline on Databricks that:
- Deploys ML jobs to different environments (dev, stage, prod) using a declarative, Terraform-based asset bundle configuration framework by Databricks.
- Automatically creates or updates Databricks Repos from a GitHub repository.
- Integrates with MLflow to track experiments and manage model versions.
- Uses Unity Catalog and Volumes for storing of models and Inference results
- Uses a Python CLI tool to encapsulate all deployment logic.
- Provides unit and integration tests to validate core functionality.
- Uses GitHub Actions for CI/CD to automate testing, code quality checks, and production deployments.

---

## Project Features

- **Environment-Specific Deployments:**  
  Each environment (dev, stage, prod) has its own bundle configuration, notebooks, and Databricks Repo.
  
- **Databricks Repos Management:**  
  The CLI tool automatically checks if a Databricks Repo exists for the target environment and creates or force-updates it to the desired Git branch.

- **Job Deployment via Databricks Asset Bundles:**  
  Job configurations are stored in YAML files (`bundle.yaml`) using the new Terraform-based schema under the `resources.jobs` key. These define job settings, notebook tasks, cluster configurations, and schedules.

- **MLflow Integration:**  
  Notebooks log parameters, metrics, and model artifacts using MLflow, with model versions managed via the MLflow Model Registry.

- **Testing:**  
  Unit tests (using `unittest` and mocks) and integration tests (which interact with an actual Databricks workspace) ensure that the deployment pipeline works as expected. Code coverage is measured using `pytest-cov`.

- **CI/CD Pipeline:**  
  GitHub Actions automates:
  - Code checkout and environment setup.
  - Installation of the Databricks CLI (via the `databricks/setup-cli` action).
  - Code quality checks (using Black and flake8).
  - Integration tests with code coverage.
  - Deployment of jobs to production when code is merged to `main`.

---



## Repository Structure

```text
wgu-assesment/
├── .github/
│   └── workflows/
│       └── ci-cd.yml              # GitHub Actions workflow for CI/CD and production deployment
├── cli_tool/
│   ├── __init__.py
│   ├── main.py                    # CLI entry point for deployment
│   ├── job_creator.py             # Contains DatabricksJobCreator class for repo management and job deployment
│   └── databricks_bundle_config/
│       ├── dev/
│       │   └── bundle.yaml        # Bundle configuration for dev jobs (Terraform-based schema)
│       ├── stage/
│       │   └── bundle.yaml        # Bundle configuration for stage jobs
│       └── prod/
│           └── bundle.yaml        # Bundle configuration for prod jobs
├── notebooks/
│   ├── dev/
│   │   ├── training.ipynb         # Development training notebook
│   │   └── inference.ipynb        # Development inference notebook
│   ├── stage/
│   │   ├── training.ipynb         # Staging training notebook
│   │   └── inference.ipynb        # Staging inference notebook
│   └── prod/
│       ├── training.ipynb         # Production training notebook
│       └── inference.ipynb        # Production inference notebook
├── tests/
│   ├── __init__.py
│   └── test_job_creator_integration.py  # Integration tests interacting with Databricks (create/update repo, deploy jobs, cleanup)
├── utilities_bash_scripts/
│   ├── validate_user.sh           # Bash script to validate user permissions on Databricks
│   └── validate_databricks_token.sh  # Bash script to validate the Databricks token
├── requirements.txt               # Python dependencies
└── README.md                      # This file

```

## Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/saikumarpochireddygari/wgu-assesment.git
   cd wgu-assesment

2. **Create a Virtual Environment & Activate it:**
   ```bash
   python -m venv venv
   source venv/bin/activate

3. **Install Python Dependencies:**
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install --only-binary=pyyaml -r requirements.txt

4. **Set Environment Variables: Ensure the following environment variables are set:**
   ```bash
   databricks configure
   DATABRICKS_HOST: e.g., https://<your-databricks-workspace>.cloud.databricks.com
   DATABRICKS_TOKEN: Your Databricks personal access token


## Usage

### Deploying Jobs via the CLI Tool

The CLI tool is located in `cli_tool/main.py` and is used to deploy environment-specific Databricks jobs. It performs the following actions:
- Determines the target environment (dev, stage, or prod) from the command-line arguments.
- Locates the appropriate bundle configuration file (e.g., `cli_tool/databricks_bundle_config/dev/bundle.yaml`).
- Ensures that the corresponding Databricks Repo exists (or updates it to the specified branch).
- Changes the working directory to the bundle configuration folder and executes the command `databricks bundle deploy` to deploy the jobs.

**Example Commands if you want to try it out locally:**

-> Note: _Make sure you setup Databricks Host and Token Locally before you test_

- **Deploy to Development:**
  ```bash
  python -m cli_tool.main deploy --env dev

- **Deploy to  Staging:**
  ```bash
  python -m cli_tool.main deploy --env stage

- **Deploy to Production:**
  ```bash
  python -m cli_tool.main deploy --env prod

- **Running unit tests:**
  ```bash
  pytest tests/test_job_creator_integration.py


## CLI Tool Overview

The project includes a Python-based CLI tool that automates the deployment of Databricks jobs across different environments. The CLI tool is built using an object-oriented approach and uses the `argparse` library to parse command-line arguments. Its main functions are:

- **Environment Determination:**  
  Based on the provided environment argument (e.g., `dev`, `stage`, or `prod`), the CLI selects the corresponding bundle configuration file (e.g., `cli_tool/databricks_bundle_config/dev/bundle.yaml`).

- **Databricks Repo Management:**  
  The CLI ensures that the appropriate Databricks Repo exists in the workspace. If the repo does not exist, it creates a new one using the Databricks Repos API. If the repo already exists, it force-updates the repo to the specified branch to pull in the latest code from GitHub.

- **Job Deployment:**  
  After ensuring the repo is updated, the CLI changes the working directory to the environment-specific bundle folder and executes the command `databricks bundle deploy` to deploy jobs defined in the bundle configuration.  
  The deployment process includes retry logic to handle transient failures and restores the original working directory after completion.

- **Extensibility:**  
  The design of the CLI tool encapsulates deployment logic in a class (e.g., `DatabricksJobCreator`), making it easier to extend, maintain, and test. Additional commands and options can be integrated without affecting the core deployment workflow.

This modular design provides a consistent and reproducible way to manage Databricks job deployments across different environments, ensuring that both code and configuration are version-controlled and deployed automatically.


## Databricks Asset Bundles & Unity Catalog

This project uses **Databricks Asset Bundles** to define and deploy jobs in a declarative, Terraform-based format. Each environment (dev, stage, prod) has its own `bundle.yaml` file located under the corresponding folder (e.g., `cli_tool/databricks_bundle_config/dev/bundle.yaml`). These bundle files specify:

- **Job Definitions:**  
  Each job is defined under `resources.jobs` with a unique identifier. The configuration includes the job’s name, schedule (defined at the job level), and tasks.  
  Each task uses `notebook_task` (with a `notebook_path`) to point to the specific notebook to run, and `new_cluster` to define the compute resources needed for the task.

- **Example (Dev Bundle):**
  ```yaml
  bundle:
    name: "my_mlops_bundle_dev"

  resources:
    jobs:
      training_job_dev:
        name: "my_training_job_dev"
        schedule:
          quartz_cron_expression: "0 10 * * * ?"
          timezone_id: "UTC"
        tasks:
          - task_key: "train_classification_model_dev"
            notebook_task:
              notebook_path: "/Repos/pochireddygari@gmail.com/wgu-assesment-dev/notebooks/dev/training"
            new_cluster:
              spark_version: "13.0.x-scala2.12"
              node_type_id: "i3.large"
              num_workers: 1

      inference_job_dev:
        name: "my_inference_job_dev"
        schedule:
          quartz_cron_expression: "0 11 * * * ?"
          timezone_id: "UTC"
        tasks:
          - task_key: "run_inference_dev"
            notebook_task:
              notebook_path: "/Repos/pochireddygari@gmail.com/wgu-assesment-dev/notebooks/dev/inference"
            new_cluster:
              spark_version: "13.0.x-scala2.12"
              node_type_id: "i3.large"
              num_workers: 1

## MLflow Integration

This project integrates with **MLflow** to enable robust experiment tracking and model management throughout the MLOps lifecycle. The MLflow integration in this project provides the following capabilities:

- **Experiment Tracking:**  
  Each training run logs important parameters, metrics, and artifacts (such as the trained model) using MLflow. This enables you to keep track of experiments and compare different model configurations.

- **Model Logging and Registration:**  
  After training, models are logged as MLflow artifacts using functions like `mlflow.sklearn.log_model()`. The model is then registered into the MLflow Model Registry under a specified model name. This process creates a new model version that is stored and versioned automatically.

- **Model Promotion via Aliases:**  
  The project uses MLflow's alias-based workflow (in place of the deprecated model stages) to manage model promotion. For instance, after a successful training run, the newly registered model version is assigned an alias such as `"production"`, so that downstream applications or inference jobs can easily reference the latest production model without needing to hard-code a version number.

### Example Workflow in a Training Notebook

Below is an example snippet from a training notebook demonstrating MLflow integration:

```python
import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature
from mlflow.tracking import MlflowClient

# Start an MLflow run with a specific experiment and tags.
with mlflow.start_run(experiment_id=experiment_id, tags=MODEL_TAGS):
    # Log hyperparameters and metrics.
    mlflow.log_params({
        "n_estimators": 100,
        "max_depth": 5,
        "random_state": 42
    })
    training_accuracy = model.score(X_train, y_train)
    mlflow.log_metric("training_accuracy", training_accuracy)
    
    # Infer the model signature and log the model.
    signature = infer_signature(X_train, model.predict(X_train))
    input_example = X_train.iloc[:5]
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="iris-model",
        signature=signature,
        input_example=input_example,
        registered_model_name=registered_model_name
    )

# Use the MLflow client to search for all versions of the registered model.
client = MlflowClient()
model_versions = client.search_model_versions(f"name='{registered_model_name}'")
latest_version = max(int(mv.version) for mv in model_versions)

# Set an alias "production" for the latest model version.
client.set_registered_model_alias(
    registered_model_name,
    "production",
    latest_version
)
```

### Testing

Integration tests run end-to-end against Databricks to verify repo and job creation, then clean up all created resources.
They can be executed with below command:

```bash
pytest tests/test_job_creator_integration.py
```


### CI/CD Pipeline (GitHub Actions)

This pipeline is designed to automate the ML production workflow by triggering on pushes to the "main" branch. It performs the following tasks sequentially:

1. **Checkout**: Retrieves the current repository.
2. **Setup**: Configures the Databricks CLI and Python environment.
3. **Install Dependencies**: Upgrades pip and installs necessary Python packages.
4. **Code Quality Checks**: Runs Black and Flake8 to ensure code style consistency.
5. **Version & Configuration**: Checks the Databricks CLI version and configures it using secrets.
6. **Permissions Validation**: Runs scripts to verify user permissions and token validity.
7. **Integration Tests**: Executes tests using pytest.
8. **Environment Determination**: Determines the deployment environment based on the branch.
9. **Deployment**: Deploys jobs to Databricks using a CLI tool.


### Changes

**Key Changes to Make as per your Use Case**

1. **notebooks/{env}/training,inference, ..**: You can add more files here, Like an ETL notebook Etc. This will be synced to databricks Repo.
2. **project.json**: Add your Databricks User Email here, This will be used to validate your permissions.
3. **requirements.txt**: Add packages here as per your use case & local env testing.
4. **Modify cli/job_creator.py**: In the Class DatabricksJobCreator, You can define your branch code to checkout for dev/prod/stage/test environments, By default im checking out main branch. Refer to  ENV_REPO_INFO Mapping.
5. **Modify cli/databricks_bundle_config/{env}/bundle.yaml**: Here you can modify the file as per your use case, You can change/edit/add mode tasks, compute, schedules, resources level permissions etc. It should be intuitive. In our case, We followed Resources --> Job --> Job Details --> Tasks Kind of structure. 
    > More Docs here: https://docs.databricks.com/aws/en/dev-tools/bundles/settings
6. **.github/workflows/ci-cd.yaml**: Feel free to add more steps here for Customizations, Some Examples can be adding more tests, add more branching strategies, Like push/merge to stage/dev branch, Can pass in dev/stage parameter to Final step of .yaml file. Right now prod flow will trigger when there is merge/push to Main branch.
7. **More paths & MLFLOW & UC Config**: Feel free to decide on team/project level naming/paths conventions as per your use cases for UC & MLFLOW. Right now its generic as per my usecase.
    > More Docs here DBAB: https://docs.databricks.com/aws/en/dev-tools/bundles/settings

    > More Docs here MLFLOW: https://mlflow.org/docs/latest/index.html

    > More Docs here Unity Catalog: https://docs.databricks.com/aws/en/data-governance/unity-catalog


### Future Improvements
- **Adding Troubleshooting Guidelines**  
- **Additional References: Best practices across teams @WGU**  
- **Some Examples for Customizations**  
- **Using tools like Poetry, TOML, and Tox for enhancing the project by improving dependency management, configuration, and testing.**

### Contact
- **Team MLOPS: mlops@wgu.edu**