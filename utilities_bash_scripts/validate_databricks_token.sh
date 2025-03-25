#!/bin/bash
# Validate Databricks credentials and permissions
set -e  # Exit immediately if any command fails
set -o pipefail  # Capture pipe command failures

# Input validation -Checking for Token & Host
if [[ -z "$DATABRICKS_HOST" || -z "$DATABRICKS_TOKEN" ]]; then
  echo "❌ Missing required environment variables: DATABRICKS_HOST or DATABRICKS_TOKEN"
  exit 1
fi

# Base API URL - Constructing API_URL
API_URL="${DATABRICKS_HOST}/api/2.0"

# Check authentication
echo "🔐 Validating Databricks authentication..."
curl -sS -X GET \
  -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  "${API_URL}/clusters/list" > /dev/null || {
  echo "❌ Authentication failed - invalid token or host"
  exit 101
}

# Check jobs permissions for User
echo "🔧 Checking jobs/create permission..."
curl -sS -X POST \
  -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  -H "Content-Type: application/json" \
  "${API_URL}/jobs/create" \
  -d '{"name":"test-job"}' > /dev/null || {
  echo "❌ Missing required permissions: jobs/create"
  exit 102
}

# Response
echo "✅ All Databricks permissions validated successfully"