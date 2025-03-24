#!/bin/bash
set -euo pipefail

# Load allowed users
ALLOWED_USERS=$(jq -r '.project_owner[]' project.json | tr '\n' '|')

# Get current user
USER_JSON=$(curl -sS -X GET \
  -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  "${DATABRICKS_HOST}/api/2.0/preview/scim/v2/Me")

# Extract email
USER_EMAIL=$(echo "${USER_JSON}" | jq -r '.emails[0].value')

# Validate authorization
if ! echo "${USER_EMAIL}" | grep -qE "(${ALLOWED_USERS%|})"; then
  echo "❌ Unauthorized user: ${USER_EMAIL}"
  exit 1
fi

echo "✅ Authorized user: ${USER_EMAIL}"