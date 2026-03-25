# Nightly Test Orchestrator

> **PLAYBOOK**: This is a gated workflow. Complete phases in order.
> Run `playbook gate` to check if the current phase's gates pass.
> Only proceed to the next phase when all gates pass.

Orchestrates nightly test runs across all Beoflow repos. Checks what changed, delegates test runs to per-repo playbooks, collects results, and pushes them to the observatory.

## Input

This playbook expects:
- Access to all Beoflow repos (sibling directories in beoflow-org)
- Observatory repo checked out at `autonomy-stack-observatory/`
- R2 credentials available via credential proxy

## Phase 1: Gather Changes (Deterministic)

Check each repo for commits in the last 24 hours.

```bash
cd /Users/daniel/GitHub/beoflow-org

REPOS="beoflow beoflow-ios beoflow-webapp"
DATE=$(date -u +%Y-%m-%d)
SINCE="24 hours ago"

for repo in $REPOS; do
  echo "=== $repo ==="
  cd /Users/daniel/GitHub/beoflow-org/$repo
  git fetch origin dev 2>/dev/null
  COMMITS=$(git log --since="$SINCE" --oneline origin/dev 2>/dev/null | wc -l | tr -d ' ')
  echo "Commits: $COMMITS"
  if [ "$COMMITS" -gt 0 ]; then
    git log --since="$SINCE" --name-only --pretty=format:"%h %s" origin/dev
  fi
  echo ""
done
```

Save the output to `.playbooks/nightly-tests/changes.md`.

```gate
test -f .playbooks/nightly-tests/changes.md
```

## Phase 2: Determine Test Scope (Non-Deterministic)

Analyze the changes from Phase 1 and decide which tests to run per repo.

For each repo with changes:

### Backend (`beoflow/`)
- Map changed files to test modules:
  - `ai_agent/` changes → run agent tests, tool tests
  - `apis/` changes → run API endpoint tests
  - `subscriptions/` changes → run subscription tests
  - `models/` changes → run all tests (model changes are cross-cutting)
  - `requirements*.txt` changes → run all tests
- If no changes, still run a smoke subset (core API health)

### iOS (`beoflow-ios/`)
- Use the file-to-screen map from the QA identity
- Determine which E2E flows are affected
- Full tab smoke test always runs regardless

### Web App (`beoflow-webapp/`)
- Map changed components/pages to E2E flows
- Run affected E2E tests + core smoke tests

Write the test plan to `.playbooks/nightly-tests/test-plan.md`:
```
## Test Plan — {date}

### Backend
- Scope: [full | partial | smoke]
- Modules: [list of test modules/files to run]
- Reason: [what changed]

### iOS
- Scope: [full | partial | smoke]
- Screens: [list of screens to test]
- Reason: [what changed]

### Web App
- Scope: [full | partial | smoke]
- Flows: [list of E2E flows to run]
- Reason: [what changed]
```

```gate
test -f .playbooks/nightly-tests/test-plan.md && grep -q "Scope:" .playbooks/nightly-tests/test-plan.md
```

## Phase 3: Run Backend Tests (Deterministic)

Execute backend tests based on the test plan.

```bash
cd /Users/daniel/GitHub/beoflow-org/beoflow

# Activate virtual environment
source .venv/bin/activate 2>/dev/null || true

# Run tests with JSON output
# If scope is "full":
python -m pytest --tb=short --json-report --json-report-file=/tmp/observatory-backend-results.json

# If scope is "partial", run specific modules:
# python -m pytest <modules from test plan> --tb=short --json-report --json-report-file=/tmp/observatory-backend-results.json

# If scope is "smoke":
# python -m pytest tests/test_api_health.py --tb=short --json-report --json-report-file=/tmp/observatory-backend-results.json
```

Transform pytest JSON report to observatory format:

```bash
python3 autonomy-stack-observatory/scripts/transform-pytest.py \
  /tmp/observatory-backend-results.json \
  /tmp/observatory-backend-formatted.json
```

```gate
test -f /tmp/observatory-backend-formatted.json && python3 -c "import json; d=json.load(open('/tmp/observatory-backend-formatted.json')); assert d.get('vertical') == 'product'"
```

## Phase 4: Run iOS Tests (Non-Deterministic)

Delegate to the iOS overnight-qa playbook, which handles:
- Booting simulator
- Building the app
- Creating Appium session
- Running smoke + focused tests
- Capturing screenshots

The iOS playbook must output results to `/tmp/observatory-ios-results.json` in observatory format, and upload screenshots to R2.

Spawn a sub-agent in the `beoflow-ios` work folder with the `beoflow-qa` identity:
```
session action="create"
  task="Run overnight QA. Output results in observatory format to /tmp/observatory-ios-results.json. Upload screenshots to R2 using autonomy-stack-observatory/scripts/upload-media.sh. Use /media/ paths in the JSON."
  workFolder="/Users/daniel/GitHub/beoflow-org/beoflow-ios"
  identity="beoflow-qa"
  taskId="nightly-ios-tests"
```

Wait for completion:
```
session action="get" taskId="nightly-ios-tests" mode="wait" timeout=1800
```

```gate
test -f /tmp/observatory-ios-results.json && python3 -c "import json; d=json.load(open('/tmp/observatory-ios-results.json')); assert d.get('source') == 'e2e-ios'"
```

## Phase 5: Run Web App Tests (Non-Deterministic)

Similar to iOS — delegate to a web E2E agent when web E2E tests exist.

Skip this phase until web E2E infrastructure is in place. Write a placeholder:

```bash
echo '{"vertical":"product","source":"e2e-web","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","summary":{"total":0,"passed":0,"failed":0,"skipped":0},"entries":[]}' > /tmp/observatory-web-results.json
```

```gate
test -f /tmp/observatory-web-results.json
```

## Phase 6: Push Results to Observatory (Deterministic)

Push all results to the observatory repo. This phase is entirely deterministic — no agent judgment.

```bash
cd /Users/daniel/GitHub/beoflow-org/autonomy-stack-observatory
DATE=$(date -u +%Y-%m-%d)

git pull origin main

# Copy results
cp /tmp/observatory-backend-formatted.json data/product/unit-backend/$DATE.json
cp /tmp/observatory-ios-results.json data/product/e2e-ios/$DATE.json
cp /tmp/observatory-web-results.json data/product/e2e-web/$DATE.json

# Commit and push
git add data/
git commit -m "data(nightly): $DATE — backend, ios, web test results"
git push origin main
```

```gate
cd /Users/daniel/GitHub/beoflow-org/autonomy-stack-observatory && git log -1 --oneline | grep -q "data(nightly)"
```

## Phase 7: Summary (Deterministic)

Output a summary of the nightly run for the morning report agent to consume:

```bash
cd /Users/daniel/GitHub/beoflow-org/autonomy-stack-observatory
DATE=$(date -u +%Y-%m-%d)

echo "## Nightly Test Summary — $DATE"
echo ""

for source in unit-backend e2e-ios e2e-web; do
  FILE="data/product/$source/$DATE.json"
  if [ -f "$FILE" ]; then
    python3 -c "
import json
d = json.load(open('$FILE'))
s = d['summary']
total = s.get('total', 0)
passed = s.get('passed', 0)
failed = s.get('failed', 0)
status = 'PASS' if failed == 0 else 'FAIL'
print(f'- **{d[\"source\"]}**: {passed}/{total} passing [{status}]')
if failed > 0:
    for e in d.get('entries', []):
        if e.get('status') == 'failed':
            print(f'  - {e[\"name\"]}: {e.get(\"error\", \"unknown\")}')
"
  fi
done
```

Write this summary to `.playbooks/nightly-tests/summary.md`.

```gate
test -f .playbooks/nightly-tests/summary.md
```
