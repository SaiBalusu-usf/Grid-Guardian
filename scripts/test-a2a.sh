#!/usr/bin/env bash
# ============================================================================
# test-a2a.sh  --  Integration test for the Shelter Specialist A2A agent
# ============================================================================

# ---------------------------------------------------------------------------
# Colours & helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

PASS="${GREEN}[PASS]${RESET}"
FAIL="${RED}[FAIL]${RESET}"
INFO="${CYAN}[INFO]${RESET}"

# Auto-detect Python and uvicorn executables
if command -v python &>/dev/null; then
    PYTHON=python
elif command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v py &>/dev/null; then
    PYTHON=py
else
    echo -e "${FAIL} No Python interpreter found"; exit 1
fi

if command -v uvicorn &>/dev/null; then
    UVICORN=uvicorn
else
    UVICORN="$PYTHON -m uvicorn"
fi

passed=0
failed=0

assert_json() {
    # Usage: assert_json "Test name" "$JSON_VAR" "python assertion expression"
    local name="$1"
    local json_data="$2"
    local assertion="$3"
    if echo "$json_data" | $PYTHON -c "$assertion" 2>/dev/null; then
        echo -e "  ${PASS} ${name}"
        ((passed++))
    else
        echo -e "  ${FAIL} ${name}"
        ((failed++))
    fi
}

assert_eq() {
    # Usage: assert_eq "Test name" "actual" "expected"
    local name="$1"
    local actual="$2"
    local expected="$3"
    if [ "$actual" = "$expected" ]; then
        echo -e "  ${PASS} ${name}"
        ((passed++))
    else
        echo -e "  ${FAIL} ${name} (got '${actual}', expected '${expected}')"
        ((failed++))
    fi
}

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PORT=8001
BASE_URL="http://localhost:${PORT}"
AGENT_DIR="$(cd "$(dirname "$0")/../backend/a2a_shelter_agent" && pwd)"
SERVER_PID=""

cleanup() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        echo -e "\n${INFO} Stopping server (PID ${SERVER_PID})..."
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# 1. Start the server
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}========================================${RESET}"
echo -e "${BOLD} Shelter Specialist A2A Agent Tests${RESET}"
echo -e "${BOLD}========================================${RESET}\n"

echo -e "${INFO} Starting server from ${AGENT_DIR} on port ${PORT}..."
cd "$AGENT_DIR"
$UVICORN server:app --host 127.0.0.1 --port "$PORT" --log-level warning &
SERVER_PID=$!
echo -e "${INFO} Server PID: ${SERVER_PID}"

# ---------------------------------------------------------------------------
# 2. Wait for server readiness
# ---------------------------------------------------------------------------
echo -e "${INFO} Waiting for server to become ready..."
MAX_WAIT=15
READY=0
for i in $(seq 1 $MAX_WAIT); do
    if curl -s "${BASE_URL}/health" > /dev/null 2>&1; then
        echo -e "${INFO} Server ready after ${i}s"
        READY=1
        break
    fi
    sleep 1
done
if [ "$READY" -eq 0 ]; then
    echo -e "${FAIL} Server failed to start within ${MAX_WAIT}s"
    exit 1
fi

# ---------------------------------------------------------------------------
# 3. Test: GET /health
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}--- Test: GET /health ---${RESET}"
HEALTH=$(curl -s "${BASE_URL}/health")
echo "$HEALTH" | $PYTHON -m json.tool 2>/dev/null || echo "$HEALTH"

assert_json "Health status is 'healthy'" \
    "$HEALTH" \
    "import sys,json; d=json.load(sys.stdin); assert d['status']=='healthy'"

assert_json "Agent name is 'shelter_specialist'" \
    "$HEALTH" \
    "import sys,json; d=json.load(sys.stdin); assert d['agent']=='shelter_specialist'"

# ---------------------------------------------------------------------------
# 4. Test: GET agent card (both paths)
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}--- Test: GET /.well-known/agent-card ---${RESET}"
CARD_WK=$(curl -s "${BASE_URL}/.well-known/agent-card")
echo "$CARD_WK" | $PYTHON -m json.tool 2>/dev/null || echo "$CARD_WK"

assert_json "Well-known agent card has correct name" \
    "$CARD_WK" \
    "import sys,json; d=json.load(sys.stdin); assert d['name']=='Shelter Specialist'"

assert_json "Well-known agent card protocol is 'a2a'" \
    "$CARD_WK" \
    "import sys,json; d=json.load(sys.stdin); assert d['protocol']=='a2a'"

echo -e "\n${BOLD}--- Test: GET /a2a/agent-card ---${RESET}"
CARD_A2A=$(curl -s "${BASE_URL}/a2a/agent-card")

assert_json "Agent card lists shelter_capacity_analysis capability" \
    "$CARD_A2A" \
    "import sys,json; d=json.load(sys.stdin); assert 'shelter_capacity_analysis' in d['capabilities']"

assert_json "Agent card has valid input_schema" \
    "$CARD_A2A" \
    "import sys,json; d=json.load(sys.stdin); assert d['input_schema']['type']=='object'"

# ---------------------------------------------------------------------------
# 5. Test: POST /a2a/execute -- basic query
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}--- Test: POST /a2a/execute (basic query) ---${RESET}"
EXEC_BASIC=$(curl -s -X POST "${BASE_URL}/a2a/execute" \
    -H "Content-Type: application/json" \
    -d '{
        "task_id": "test-001",
        "message": {
            "role": "user",
            "content": {}
        }
    }')
echo "$EXEC_BASIC" | $PYTHON -m json.tool 2>/dev/null || echo "$EXEC_BASIC"

assert_json "Basic execute returns status 'completed'" \
    "$EXEC_BASIC" \
    "import sys,json; d=json.load(sys.stdin); assert d['status']=='completed'"

assert_json "Task ID matches 'test-001'" \
    "$EXEC_BASIC" \
    "import sys,json; d=json.load(sys.stdin); assert d['task_id']=='test-001'"

assert_json "Returns all 4 shelters" \
    "$EXEC_BASIC" \
    "import sys,json; d=json.load(sys.stdin); assert len(d['result']['shelters'])==4"

assert_json "Total available capacity is positive" \
    "$EXEC_BASIC" \
    "import sys,json; d=json.load(sys.stdin); assert d['result']['total_available_capacity']>0"

assert_json "Identifies at least one critical shelter" \
    "$EXEC_BASIC" \
    "import sys,json; d=json.load(sys.stdin); assert len(d['result']['critical_shelters'])>0"

# ---------------------------------------------------------------------------
# 6. Test: POST /a2a/execute -- filtered by accessibility
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}--- Test: POST /a2a/execute (full_ada filter) ---${RESET}"
EXEC_ADA=$(curl -s -X POST "${BASE_URL}/a2a/execute" \
    -H "Content-Type: application/json" \
    -d '{
        "task_id": "test-002",
        "message": {
            "role": "user",
            "content": {
                "accessibility_required": "full_ada",
                "capacity_needed": 200,
                "scenario": "hurricane flooding"
            }
        }
    }')
echo "$EXEC_ADA" | $PYTHON -m json.tool 2>/dev/null || echo "$EXEC_ADA"

assert_json "ADA filter returns only full_ada shelters" \
    "$EXEC_ADA" \
    "
import sys, json
d = json.load(sys.stdin)
shelters = d['result']['shelters']
assert len(shelters) > 0
for s in shelters:
    assert s['accessibility'] == 'full_ada', f\"Got {s['accessibility']}\"
"

assert_json "Scenario-aware recommendations mention flooding" \
    "$EXEC_ADA" \
    "
import sys, json
d = json.load(sys.stdin)
recs = ' '.join(d['result']['recommendations'])
assert 'flood' in recs.lower() or 'hurricane' in recs.lower()
"

# ---------------------------------------------------------------------------
# 7. Test: POST /a2a/execute -- validation error
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}--- Test: POST /a2a/execute (validation error) ---${RESET}"
EXEC_BAD=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/a2a/execute" \
    -H "Content-Type: application/json" \
    -d '{
        "task_id": "test-003",
        "message": {
            "role": "user",
            "content": {
                "accessibility_required": "invalid_value"
            }
        }
    }')
assert_eq "Invalid accessibility_required returns HTTP 422" "$EXEC_BAD" "422"

# ---------------------------------------------------------------------------
# 8. Test: GET /a2a/tasks/{task_id}
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}--- Test: GET /a2a/tasks/test-001 ---${RESET}"
TASK_RESULT=$(curl -s "${BASE_URL}/a2a/tasks/test-001")
echo "$TASK_RESULT" | $PYTHON -m json.tool 2>/dev/null || echo "$TASK_RESULT"

assert_json "Task retrieval returns correct task_id" \
    "$TASK_RESULT" \
    "import sys,json; d=json.load(sys.stdin); assert d['task_id']=='test-001'"

assert_json "Retrieved task status is 'completed'" \
    "$TASK_RESULT" \
    "import sys,json; d=json.load(sys.stdin); assert d['status']=='completed'"

assert_json "Retrieved task agent is 'shelter_specialist'" \
    "$TASK_RESULT" \
    "import sys,json; d=json.load(sys.stdin); assert d['agent']=='shelter_specialist'"

assert_json "Task metadata includes execution_time_ms" \
    "$TASK_RESULT" \
    "import sys,json; d=json.load(sys.stdin); assert d['metadata']['execution_time_ms']>=0"

# ---------------------------------------------------------------------------
# 9. Test: GET /a2a/tasks/{task_id} -- not found
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}--- Test: GET /a2a/tasks/nonexistent ---${RESET}"
NOT_FOUND_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/a2a/tasks/nonexistent")
assert_eq "Nonexistent task returns HTTP 404" "$NOT_FOUND_CODE" "404"

# ---------------------------------------------------------------------------
# 10. Test: POST /a2a/execute -- string message (scenario shorthand)
# ---------------------------------------------------------------------------
echo -e "\n${BOLD}--- Test: POST /a2a/execute (string message) ---${RESET}"
EXEC_STR=$(curl -s -X POST "${BASE_URL}/a2a/execute" \
    -H "Content-Type: application/json" \
    -d '{
        "task_id": "test-004",
        "message": {
            "role": "user",
            "content": "earthquake emergency"
        }
    }')

assert_json "String content message executes successfully" \
    "$EXEC_STR" \
    "import sys,json; d=json.load(sys.stdin); assert d['status']=='completed'"

assert_json "Earthquake scenario triggers relevant recommendations" \
    "$EXEC_STR" \
    "
import sys, json
d = json.load(sys.stdin)
recs = ' '.join(d['result']['recommendations'])
assert 'earthquake' in recs.lower()
"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
total=$((passed + failed))
echo -e "\n${BOLD}========================================${RESET}"
echo -e "${BOLD} Results: ${passed}/${total} passed${RESET}"
if [ "$failed" -gt 0 ]; then
    echo -e " ${RED}${failed} test(s) failed${RESET}"
fi
echo -e "${BOLD}========================================${RESET}\n"

exit "$failed"
