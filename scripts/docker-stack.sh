#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$ROOT_DIR/docker-stack.log"
cd "$ROOT_DIR"
touch "$LOG_FILE"
COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.host.yml)

run_logged() {
  {
    printf '\n[%s] ' "$(date --iso-8601=seconds)"
    printf '%q ' "$@"
    printf '\n'
  } | tee -a "$LOG_FILE"
  "$@" 2>&1 | tee -a "$LOG_FILE"
}

capture_container_logs() {
  "${COMPOSE[@]}" logs --no-color --timestamps --tail=100 2>&1 | tee -a "$LOG_FILE"
}

start_stack() {
  run_logged "${COMPOSE[@]}" up --build -d
  capture_container_logs
  printf '\nFrontend: http://localhost:8501\nBackend health: http://localhost:7860/healthz\nLog: %s\n' "$LOG_FILE"
}

stop_stack() {
  capture_container_logs
  run_logged "${COMPOSE[@]}" down
  printf '\nDocker stack stopped. Log: %s\n' "$LOG_FILE"
}

action="${1:-toggle}"
case "$action" in
  start)
    start_stack
    ;;
  stop)
    stop_stack
    ;;
  toggle)
    if [[ -n $("${COMPOSE[@]}" ps --status running -q) ]]; then
      stop_stack
    else
      start_stack
    fi
    ;;
  *)
    printf 'Usage: %s [start|stop|toggle]\n' "$0" >&2
    exit 2
    ;;
esac