```bash
#!/usr/bin/env bash
set -euo pipefail

# Detect privilege level
if [ "$(id -u)" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Set workspace path (from container info)
WORKSPACE="/home/kavia/workspace/code-generation/food-delivery-app-14946-15105/PromotionService"
cd "$WORKSPACE"

# === COMMAND: INSTALL ===
# Set global environment variables for headless testing and dev runtime
echo 'export CHROME_BIN=chromium' | $SUDO tee /etc/profile.d/chrome_bin.sh > /dev/null
echo 'export NODE_ENV=development' | $SUDO tee /etc/profile.d/node_env.sh > /dev/null
$SUDO chmod +x /etc/profile.d/chrome_bin.sh /etc/profile.d/node_env.sh

# === COMMAND: SCAFFOLD ===
# Scaffold React app if missing, choosing npm/yarn per lockfile
if [ ! -f "package.json" ]; then
  if [ -f "yarn.lock" ]; then
    yarn create react-app . --silent
  else
    npx create-react-app . --quiet
  fi
fi

# === COMMAND: DEPS ===
# Install dependencies based on lockfile presence
if [ -f "yarn.lock" ] && [ -f "package-lock.json" ]; then
  echo "WARNING: Both yarn.lock and package-lock.json found. Defaulting to yarn install." >&2
  yarn --silent --check-files
elif [ -f "yarn.lock" ]; then
  yarn --silent --check-files
else
  npm i --quiet --no-progress
fi

# === COMMAND: BUILD ===
# Build the React application
npm run build -- --quiet

# === COMMAND: TEST ===
# Run tests in headless mode, minimal output
npm test -- --ci --watchAll=false --silent

# === COMMAND: START ===
# Canonical start of React dev server (no backgrounding, no verification)
npm start

# === COMMAND: VALIDATE ===
# Start dev server in background, verify health, then cleanly stop it
TMP_VALIDATE_PID=""
npm start -- --port 3000 >.validate-react.log 2>&1 & TMP_VALIDATE_PID=$!
timeout=20; while ! curl --silent --fail http://localhost:3000 > /dev/null; do
  sleep 1; timeout=$((timeout-1)); [ $timeout -le 0 ] && { echo "ERROR: React dev server failed to start on port 3000" >&2; kill $TMP_VALIDATE_PID; exit 1; }
done
echo "React dev server is running and reachable on port 3000."
kill $TMP_VALIDATE_PID
wait $TMP_VALIDATE_PID 2>/dev/null || true
rm -f .validate-react.log

# === COMMAND: STOP ===
# No persistent background process to stop; noop for robustness
true
```