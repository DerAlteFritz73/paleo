#!/bin/bash
# Polled by cron every minute. Deploys the paleo-prod container whenever
# HEAD has moved past what was last deployed.
#
# Deploys are triggered off HEAD vs a local marker file (.deployed-commit),
# not off comparing local main to origin/main: commits are often made
# directly in this checkout (e.g. by Claude Code working in prod), which
# advances local main and origin/main together and would leave a diff-based
# trigger permanently silent. Fetching + fast-forwarding first still picks
# up commits pushed from elsewhere.
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
DEPLOYED_FILE="$REPO_DIR/.deployed-commit"

exec 9>"$LOCK_FILE"
flock -n 9 || exit 0

cd "$REPO_DIR"

git fetch origin main --quiet

if ! git pull --ff-only origin main >> "$LOG_FILE" 2>&1; then
    echo "$(date -Iseconds) PULL SKIPPED: working tree has local changes, cannot fast-forward" >> "$LOG_FILE"
fi

HEAD=$(git rev-parse HEAD)
DEPLOYED=$(cat "$DEPLOYED_FILE" 2>/dev/null || echo "")

[ "$HEAD" = "$DEPLOYED" ] && exit 0

echo "$(date -Iseconds) new commit to deploy: ${DEPLOYED:-<none>} -> $HEAD" >> "$LOG_FILE"

echo "$(date -Iseconds) rebuilding container" >> "$LOG_FILE"
docker compose up -d --build >> "$LOG_FILE" 2>&1
echo "$HEAD" > "$DEPLOYED_FILE"
echo "$(date -Iseconds) deploy complete, now at $HEAD" >> "$LOG_FILE"
