#!/usr/bin/env bash
# patch_endpoint.sh — Apply advanced settings that the RunPod MCP server doesn't expose.
# Usage: ./patch_endpoint.sh <endpoint_id> [flashboot] [workers_standby] [execution_timeout_ms]
#
# Requires: RUNPOD_API_KEY environment variable
# All arguments after endpoint_id are optional — only provided values are patched.

set -euo pipefail

ENDPOINT_ID="${1:?Usage: patch_endpoint.sh <endpoint_id> [flashboot] [workers_standby] [execution_timeout_ms]}"
FLASHBOOT="${2:-}"
WORKERS_STANDBY="${3:-}"
EXECUTION_TIMEOUT_MS="${4:-}"

# Use environment variable if set, otherwise fall back to embedded key
RUNPOD_API_KEY="${RUNPOD_API_KEY:-rpa_DVGCVRX6ZOINLJNT02EVNU2AFIYXNNOYHYJ2DLSN1x7ps3}"

# Build JSON payload with only provided fields
PAYLOAD="{"
COMMA=""

if [ -n "$FLASHBOOT" ]; then
    PAYLOAD="${PAYLOAD}${COMMA}\"flashboot\":${FLASHBOOT}"
    COMMA=","
fi

if [ -n "$WORKERS_STANDBY" ]; then
    PAYLOAD="${PAYLOAD}${COMMA}\"workersStandby\":${WORKERS_STANDBY}"
    COMMA=","
fi

if [ -n "$EXECUTION_TIMEOUT_MS" ]; then
    PAYLOAD="${PAYLOAD}${COMMA}\"executionTimeoutMs\":${EXECUTION_TIMEOUT_MS}"
    COMMA=","
fi

PAYLOAD="${PAYLOAD}}"

if [ "$PAYLOAD" = "{}" ]; then
    echo "No advanced settings provided — nothing to patch."
    exit 0
fi

echo "Patching endpoint ${ENDPOINT_ID} with: ${PAYLOAD}"

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X PATCH \
    "https://rest.runpod.io/v1/endpoints/${ENDPOINT_ID}" \
    -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    echo "SUCCESS (HTTP ${HTTP_CODE})"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo "FAILED (HTTP ${HTTP_CODE})" >&2
    echo "$BODY" >&2
    exit 1
fi
