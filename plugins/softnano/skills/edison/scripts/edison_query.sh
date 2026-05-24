#!/usr/bin/env bash
set -euo pipefail

# Edison Research Query Script
# Authenticates, submits a literature search, polls until complete, outputs clean JSON.

BASE_URL="https://api.platform.edisonscientific.com"
POLL_INTERVAL=15
MAX_WAIT=600

usage() {
    cat >&2 <<EOF
Usage: $0 --query <question> [--continue-from <task_id>]

Options:
  --query          The research question to ask Edison
  --continue-from  Task ID of a previous query to continue from
EOF
    exit 1
}

die() {
    echo "{\"error\": \"$1\"}" >&2
    exit 1
}

# --- Parse arguments ---

QUERY=""
CONTINUE_FROM=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --query) QUERY="$2"; shift 2 ;;
        --continue-from) CONTINUE_FROM="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
done

[[ -z "$QUERY" ]] && die "No --query provided"

# --- Check prerequisites ---

if [[ -z "${EDISON_PLATFORM_API_KEY:-}" ]]; then
    echo '{"error": "EDISON_PLATFORM_API_KEY not set. Add it to the agent environment."}'
    exit 0
fi

if ! command -v jq &>/dev/null; then
    die "jq is required but not installed"
fi

# --- Step 1: Authenticate ---

AUTH_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg k "$EDISON_PLATFORM_API_KEY" '{api_key: $k}')")

TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token // empty')
if [[ -z "$TOKEN" ]]; then
    echo "$AUTH_RESPONSE" | jq '{error: "Authentication failed", details: .}' >&2
    exit 1
fi

echo "Authenticated successfully" >&2

# --- Step 2: Submit task ---

if [[ -n "$CONTINUE_FROM" ]]; then
    BODY=$(jq -n --arg q "$QUERY" --arg tid "$CONTINUE_FROM" \
        '{name: "job-futurehouse-paperqa3", query: $q, runtime_config: {continued_job_id: $tid}}')
else
    BODY=$(jq -n --arg q "$QUERY" \
        '{name: "job-futurehouse-paperqa3", query: $q}')
fi

SUBMIT_RESPONSE=$(curl -s -X POST "$BASE_URL/v0.1/crows" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "x-client: sdk" \
    -d "$BODY")

TASK_ID=$(echo "$SUBMIT_RESPONSE" | jq -r '.trajectory_id // empty')
if [[ -z "$TASK_ID" ]]; then
    echo "$SUBMIT_RESPONSE" | jq '{error: "Task submission failed", details: .}' >&2
    exit 1
fi

echo "Submitted task $TASK_ID — polling every ${POLL_INTERVAL}s (max ${MAX_WAIT}s)..." >&2

# --- Step 3: Poll until done ---

ELAPSED=0
while [[ $ELAPSED -lt $MAX_WAIT ]]; do
    sleep "$POLL_INTERVAL"
    ELAPSED=$((ELAPSED + POLL_INTERVAL))

    POLL_RESPONSE=$(curl -s "$BASE_URL/v0.1/trajectories/$TASK_ID?lite=true" \
        -H "Authorization: Bearer $TOKEN")

    STATUS=$(echo "$POLL_RESPONSE" | jq -r '.status // "unknown"')

    case "$STATUS" in
        success)
            echo "Task completed after ${ELAPSED}s" >&2
            break
            ;;
        fail|cancelled|truncated)
            echo "{\"error\": \"Task ${STATUS} after ${ELAPSED}s\", \"task_id\": \"$TASK_ID\"}"
            exit 1
            ;;
        *)
            echo "Status: $STATUS (${ELAPSED}s elapsed)" >&2
            ;;
    esac
done

if [[ $ELAPSED -ge $MAX_WAIT ]]; then
    echo "{\"error\": \"Timed out after ${MAX_WAIT}s\", \"task_id\": \"$TASK_ID\"}"
    exit 1
fi

# --- Step 4: Fetch full response and extract answer ---

FULL_RESPONSE=$(curl -s "$BASE_URL/v0.1/trajectories/$TASK_ID" \
    -H "Authorization: Bearer $TOKEN")

echo "$FULL_RESPONSE" | jq --arg tid "$TASK_ID" '{
    task_id: $tid,
    formatted_answer: .environment_frame.state.state.response.answer.formatted_answer,
    answer: .environment_frame.state.state.response.answer.answer,
    has_successful_answer: .environment_frame.state.state.response.answer.has_successful_answer
}'
