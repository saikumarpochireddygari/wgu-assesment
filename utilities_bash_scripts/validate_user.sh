#!/bin/bash
set -euo pipefail

# Load allowed users from project.json file
ALLOWED_USERS=$(jq -r '.project_owner[]' project.json | tr '\n' '|')

# Get current user details
USER_JSON=$(curl -sS -X GET \
  -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  "${DATABRICKS_HOST}/api/2.0/preview/scim/v2/Me")

# Extract email from json response
USER_EMAIL=$(echo "${USER_JSON}" | jq -r '.emails[0].value')

# Validating authorization
if ! echo "${USER_EMAIL}" | grep -qE "(${ALLOWED_USERS%|})"; then
  echo "❌ Unauthorized user: ${ALLOWED_USERS%|}"
  exit 1
fi

# Response
echo "✅ Authorized user: ${ALLOWED_USERS%|}"