#!/bin/bash

# Iris frontend (Vite). Restarts itself if it exits so the App panel always recovers.
# Logs go to /tmp/vite.log - view them from the terminal with: tail -f /tmp/vite.log
(
  cd /code/iris/frontend || exit 1
  npm install
  while true; do
    npm run dev -- --host 0.0.0.0 --port 3000 --strictPort
    sleep 2
  done
) > /tmp/vite.log 2>&1 &

WELCOME='echo; echo "  Redis Iris demo - run these from /code/iris:"; echo "    make setup    # generate data, load Redis, seed memory + cache (needs .env credentials)"; echo "    make reset    # reload data for the current domain"; echo "    make domains  # list demo domains"; echo "    pytest        # run the unit tests"; echo'

# Create or recreate the tmux session
create_session() {
  tmux -f /etc/tmux.conf new-session -d -s workshop -c /code/iris
  tmux send-keys -t workshop "clear; $WELCOME" Enter
}

# Initial session creation
if ! tmux has-session -t workshop 2>/dev/null; then
  create_session
fi

# Start ttyd with a wrapper script that ensures session exists before attaching
# This allows multiple clients (no --once) while still recreating the session if it dies
export WELCOME
ttyd -W -p 7681 bash -c '
  if ! tmux -f /etc/tmux.conf has-session -t workshop 2>/dev/null; then
    tmux -f /etc/tmux.conf new-session -d -s workshop -c /code/iris
    tmux send-keys -t workshop "clear; $WELCOME" Enter
  fi
  exec tmux -f /etc/tmux.conf attach-session -t workshop
'
