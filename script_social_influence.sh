#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Logging setup
# -----------------------------
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/run_$(date '+%Y%m%d_%H%M%S').log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "Logging to $LOG_FILE"


# -----------------------------
# Config 
# -----------------------------
CASES=(social_influence)
SETS=(set_a set_b)
MODEL="gpt-5"
REASONING_MODE=(minimal high)

# Starting port for FastAPI servers
START_PORT=8000

# -----------------------------
# Seed pool (fixed 200 numbers)
# -----------------------------
SEED_FILE="social_influence_seeds.txt"

# Read seeds file into an array (POSIX-compatible)
SEEDS=()
while IFS= read -r line || [ -n "$line" ]; do
  SEEDS+=("$line")
done < "$SEED_FILE"
SEED_COUNT=${#SEEDS[@]}
if [[ $SEED_COUNT -lt 1 ]]; then
  echo "seeds.txt is empty. Populate it with at least one integer per line." >&2
  exit 1
fi

# Initialize seed counter
SEED_INDEX=0

# -----------------------------
# Helpers
# -----------------------------
port_pids() { lsof -ti tcp:"$1" || true; }             
wait_for_port_up() {                                   # wait until server listens
  local host="${1}" port="${2}" timeout="${3:-30}" t=0
  while ! nc -z "$host" "$port" >/dev/null 2>&1; do
    sleep 0.5; t=$((t+1)); [[ $t -ge $((timeout*2)) ]] && return 1
  done
}
wait_for_port_down() {                                 # wait until port is freed
  local port="${1}" timeout="${2:-30}" t=0
  while port_pids "$port" >/dev/null; do
    sleep 0.5; t=$((t+1)); [[ $t -ge $((timeout*2)) ]] && return 1
  done
}
stop_server_on_port() {                                # TERM → wait → KILL
  local port="$1"
  local pids
  pids=$(port_pids "$port")
  [[ -z "$pids" ]] && return 0
  echo "Stopping processes on port $port: $pids"
  kill $pids 2>/dev/null || true
  sleep 1
  if port_pids "$port" >/dev/null; then
    echo "Forcing kill on port $port..."
    kill -9 $(port_pids "$port") 2>/dev/null || true
  fi
  wait_for_port_down "$port" 10 || echo "Warning: port $port still busy."
}

cleanup() {                                            # safety on exit/ctrl-c
  for p in $(port_pids "$PORT"); do kill $p 2>/dev/null || true; done
}
trap cleanup EXIT INT TERM

# -----------------------------
# Main loop
# -----------------------------
ROOT_DIR="$(pwd)"
PORT="$START_PORT"

for CASE in "${CASES[@]}"; do
  for SET in "${SETS[@]}"; do
    APP_DIR="${ROOT_DIR}/${CASE}/${SET}"

    if [[ ! -f "${APP_DIR}/app.py" ]]; then
      echo "Skipping ${CASE}/${SET}: app.py not found at ${APP_DIR}/app.py"
      continue
    fi

    echo "---------------------------------------------"
    echo "Case: ${CASE} | Set: ${SET} | Port: ${PORT}"
    echo "Starting FastAPI dev server..."
    echo "---------------------------------------------"

    # Ensure port is clear
    stop_server_on_port "$PORT"

    # Run FastAPI dev server in background
    ( cd "${APP_DIR}" && uvicorn app:app --host 127.0.0.1 --port "${PORT}") &
    SERVER_PID=$!

    # Give the server a few seconds to boot
    sleep 5

    # Run experiments for each reasoning mode, 50 iterations each
    for REASONING in "${REASONING_MODE[@]}"; do
      for i in $(seq 1 50); do
        SEED="${SEEDS[$SEED_INDEX]}"
        
        # Check if conversation directory already exists
        CONV_PATH="${APP_DIR}/conversations/model-${MODEL}-reasoning-${REASONING}-seed-${SEED}"
        if [[ -d "$CONV_PATH" ]]; then
          echo "Skipping (already exists): ${CASE}/${SET}/conversations/model-${MODEL}-reasoning-${REASONING}-seed-${SEED}"
          SEED_INDEX=$((SEED_INDEX + 1))
          continue
        fi
        
        echo "Running experiment: --case ${CASE} --set ${SET} --model ${MODEL} --reasoning ${REASONING} --seed ${SEED} (iteration $i, seed index $SEED_INDEX)"
        ( cd "${ROOT_DIR}" && python experiment.py \
            --case "${CASE}" \
            --set "${SET}" \
            --model "${MODEL}" \
            --reasoning "${REASONING}" \
            --seed "${SEED}" )
        SEED_INDEX=$((SEED_INDEX + 1))
      done
    done

    # Stop the FastAPI server for this set
    echo "Shutting down FastAPI server (pid ${SERVER_PID})..."
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" 2>/dev/null || true

  done
done

echo "All done ✅"


