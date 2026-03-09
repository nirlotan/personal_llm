#!/usr/bin/env zsh
# start.sh — start backend + frontend locally and open the browser

set -e

SCRIPT_DIR="${0:A:h}"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=3000
FRONTEND_URL="http://localhost:$FRONTEND_PORT"

# ── helpers ────────────────────────────────────────────────────────────────────

log()  { print -P "%F{cyan}[start.sh]%f $*"; }
warn() { print -P "%F{yellow}[start.sh]%f $*"; }
die()  { print -P "%F{red}[start.sh]%f $*" >&2; exit 1; }

cleanup() {
  log "Shutting down..."
  [[ -n "$BACKEND_PID"  ]] && kill "$BACKEND_PID"  2>/dev/null
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null
  wait 2>/dev/null
  log "Done."
}
trap cleanup INT TERM EXIT

# ── preflight ──────────────────────────────────────────────────────────────────

[[ -f "$BACKEND_DIR/.env" ]] || die "backend/.env not found — copy backend/.env.example and fill in values."

# Activate backend virtualenv
VENV="$BACKEND_DIR/.venv"
[[ -d "$VENV" ]] || die ".venv not found — run: cd backend && python3 -m venv .venv && pip install -r requirements.txt"
source "$VENV/bin/activate"

# Check frontend deps
[[ -d "$FRONTEND_DIR/node_modules" ]] || die "node_modules not found — run: cd frontend && npm install"

# ── start backend ──────────────────────────────────────────────────────────────

log "Starting backend on port $BACKEND_PORT..."

(
  cd "$BACKEND_DIR"
  uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT" --reload
) &
BACKEND_PID=$!

# Wait for backend to become ready (max 30 s)
log "Waiting for backend to be ready..."
for i in {1..30}; do
  if curl -sf "http://127.0.0.1:$BACKEND_PORT/api/health" >/dev/null 2>&1; then
    log "Backend is up."
    break
  fi
  sleep 1
  if (( i == 30 )); then
    die "Backend did not start within 30 seconds."
  fi
done

# ── start frontend ─────────────────────────────────────────────────────────────

log "Starting frontend on port $FRONTEND_PORT..."

(
  cd "$FRONTEND_DIR"
  npm run dev -- --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

# Wait for frontend to become ready (max 60 s — Next.js compiles on first start)
log "Waiting for frontend to be ready..."
for i in {1..60}; do
  if curl -sf "$FRONTEND_URL" >/dev/null 2>&1; then
    log "Frontend is up."
    break
  fi
  sleep 1
  if (( i == 60 )); then
    warn "Frontend health check timed out — opening browser anyway."
    break
  fi
done

# ── open browser ───────────────────────────────────────────────────────────────

log "Opening $FRONTEND_URL in the default browser..."
open "$FRONTEND_URL"

# ── keep running ──────────────────────────────────────────────────────────────

log "Both services running. Press Ctrl-C to stop."
wait
