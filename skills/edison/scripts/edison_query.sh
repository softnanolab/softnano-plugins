#!/usr/bin/env bash
set -euo pipefail

# Edison Research Query Script
# Authenticates, submits a literature search, polls until complete, outputs clean JSON.

BASE_URL="https://api.platform.edisonscientific.com"
POLL_INTERVAL=15
MAX_WAIT=600

usage() {
    cat >&2 <<EOF
Usage: $0 --query <question> [--continue-from <task_id>] [--max-wait <seconds>] [--poll-interval <seconds>]
       $0 --task-id <task_id> [--max-wait <seconds>] [--poll-interval <seconds>]

Options:
  --query          The research question to ask Edison
  --continue-from  Task ID of a previous query to continue from
  --task-id        Poll/fetch an existing Edison task without submitting a new one
  --max-wait       Maximum local wait time in seconds before returning a resumable status
  --poll-interval  Poll interval in seconds
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
TASK_ID=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --query) QUERY="$2"; shift 2 ;;
        --continue-from) CONTINUE_FROM="$2"; shift 2 ;;
        --task-id) TASK_ID="$2"; shift 2 ;;
        --max-wait) MAX_WAIT="$2"; shift 2 ;;
        --poll-interval) POLL_INTERVAL="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
done

[[ -z "$QUERY" && -z "$TASK_ID" ]] && die "Provide either --query or --task-id"

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

fetch_answer() {
    local task_id="$1"
    local full_response
    full_response=$(curl -s "$BASE_URL/v0.1/trajectories/$task_id" \
        -H "Authorization: Bearer $TOKEN")

    echo "$full_response" | jq --arg tid "$task_id" '{
        task_id: $tid,
        status: "success",
        formatted_answer: .environment_frame.state.state.response.answer.formatted_answer,
        answer: .environment_frame.state.state.response.answer.answer,
        has_successful_answer: .environment_frame.state.state.response.answer.has_successful_answer
    }'
}

poll_task() {
    local task_id="$1"
    local elapsed=0

    while true; do
        local poll_response status
        poll_response=$(curl -s "$BASE_URL/v0.1/trajectories/$task_id?lite=true" \
            -H "Authorization: Bearer $TOKEN")

        status=$(echo "$poll_response" | jq -r '.status // "unknown"')

        case "$status" in
            success)
                echo "Task completed after ${elapsed}s" >&2
                fetch_answer "$task_id"
                return 0
                ;;
            fail|cancelled|truncated)
                jq -n --arg task_id "$task_id" --arg status "$status" --arg elapsed "$elapsed" \
                    '{error: ("Task " + $status + " after " + $elapsed + "s"), task_id: $task_id, status: $status}'
                return 1
                ;;
            *)
                if [[ "$MAX_WAIT" -le 0 || "$elapsed" -ge "$MAX_WAIT" ]]; then
                    jq -n \
                        --arg task_id "$task_id" \
                        --arg status "$status" \
                        --arg elapsed "$elapsed" \
                        --arg max_wait "$MAX_WAIT" \
                        --arg resume_command "$0 --task-id $task_id" \
                        '{
                            task_id: $task_id,
                            status: $status,
                            recoverable: true,
                            has_successful_answer: false,
                            formatted_answer: null,
                            answer: null,
                            message: ("Local wait limit reached after " + $elapsed + "s (max " + $max_wait + "s); Edison is still running. Poll this task again with resume_command."),
                            resume_command: $resume_command
                        }'
                    return 0
                fi

                echo "Status: $status (${elapsed}s elapsed)" >&2
                sleep "$POLL_INTERVAL"
                elapsed=$((elapsed + POLL_INTERVAL))
                ;;
        esac
    done
}

if [[ -n "$TASK_ID" ]]; then
    echo "Polling existing task $TASK_ID every ${POLL_INTERVAL}s (max ${MAX_WAIT}s)..." >&2
    poll_task "$TASK_ID"
    exit $?
fi

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
poll_task "$TASK_ID"
