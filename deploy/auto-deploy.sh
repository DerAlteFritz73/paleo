#!/bin/bash
# Polled by cron every minute. Deploys the paleo-prod container whenever
# origin/main has moved past what's currently checked out here.
#
# Uses `git pull --ff-only` rather than a hard reset: if the working tree
# has local uncommitted changes (e.g. mid-edit in VS Code) that would
# conflict with the incoming commit, the pull simply fails and this run
# is skipped — nothing is ever discarded. It'll deploy on the next poll
# once the tree is clean again.
set -euo pipefail

REPO_DIR="/var/www/prod/paleo"
LOG_FILE="$REPO_DIR/.deploy.log"
LOCK_FILE="/tmp/paleo-prod-deploy.lock"

exec 9>"$LOCK_FILE"
flock -n 9 || exit 0

cd "$REPO_DIR"

git fetch origin main --quiet

LOCAL=$(git rev-parse main)
REMOTE=$(git rev-parse origin/main)

[ "$LOCAL" = "$REMOTE" ] && exit 0

echo "$(date -Iseconds) new commit detected: $LOCAL -> $REMOTE" >> "$LOG_FILE"

if ! git pull --ff-only origin main >> "$LOG_FILE" 2>&1; then
    echo "$(date -Iseconds) DEPLOY SKIPPED: working tree has local changes, cannot fast-forward" >> "$LOG_FILE"
    exit 1
fi

echo "$(date -Iseconds) rebuilding container" >> "$LOG_FILE"
docker compose up -d --build >> "$LOG_FILE" 2>&1
echo "$(date -Iseconds) deploy complete, now at $(git rev-parse HEAD)" >> "$LOG_FILE"
