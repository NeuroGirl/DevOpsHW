# !/bin/bash

SECRET_PATH="$1"
SECRET_KEY="$2"

if [ -z "$VAULT_ADDR" ]; then
  echo "Error: VAULT_ADDR is not set." >&2
  exit 1
fi
if [ -z "$VAULT_TOKEN" ]; then
  echo "Error: VAULT_TOKEN is not set." >&2
  exit 1
fi
if [ -z "$SECRET_PATH" ] || [ -z "$SECRET_KEY" ]; then
  echo "Usage: fetch-vault-secret.sh <vault_secret_path> <vault_secret_key>" >&2
  exit 1
fi

SECRET_VALUE=$(vault kv get -format=json "${SECRET_PATH}" | jq -r ".data.data[\"${SECRET_KEY}\"]")

if [ -z "$SECRET_VALUE" ]; then
  echo "Error: Failed to retrieve secret '${SECRET_KEY}' from '${SECRET_PATH}' in Vault." >&2
  exit 1
fi

echo "$SECRET_VALUE"
