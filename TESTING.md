# FocusGuard Testing Guide

This document covers automated tests (backend API), manual testing (API + Extension), and end-to-end flow validation.

## 1. Backend API Tests (pytest)

### Setup
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Copy .env.example to .env and adjust DATABASE_URL if needed
cp backend/.env.example backend/.env
```

### Run tests
```bash
# From repo root
pytest backend/tests/ -v

# With coverage
pytest backend/tests/ --cov=app --cov-report=html
```

### Available test files
- `backend/tests/test_auth.py` — register, login endpoints
- `backend/tests/test_blocking.py` — add/remove blocked sites, log attempts
- `backend/tests/test_accountability.py` — send approval, approve access
- `backend/tests/test_reporting.py` — weekly report endpoint
- `backend/tests/conftest.py` — shared fixtures (test DB, client, user)

## 2. Manual API Testing (curl)

### Start the backend
```bash
# Using Docker Compose (recommended)
docker compose up -d --build

# Or local (requires venv + deps + DATABASE_URL env)
uvicorn app.main:app --reload --port 8000
```

### Health check
```bash
curl http://localhost:8000/health
# expect: {"status":"ok"}
```

### Auth flow
```bash
# Register
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"StrongPassw0rd123!"}'
# response: {"access_token":"...","token_type":"bearer"}

# Save token for remaining tests
TOKEN="paste_token_here"

# Login (get new token)
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"StrongPassw0rd123!"}'
```

### Blocking flow
```bash
TOKEN="your_token"

# Add blocked site
curl -X POST http://localhost:8000/add-blocked-site \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain":"youtube.com"}'
# response: {"id":"...","domain":"youtube.com","is_active":true,"created_at":"..."}

# Add another (idempotent — should return same site)
curl -X POST http://localhost:8000/add-blocked-site \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain":"youtube.com"}'

# Remove blocked site
curl -X POST http://localhost:8000/remove-blocked-site \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain":"youtube.com"}'
# response: {"status":"removed"}
```

### Attempt logging
```bash
TOKEN="your_token"

# Log a block attempt
curl -X POST http://localhost:8000/log-attempt \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain":"reddit.com",
    "url":"https://reddit.com/r/funny",
    "tab_id":123,
    "source":"extension",
    "reason":"blocked"
  }'
# response: {"status":"logged"}
```

### Accountability flow
```bash
TOKEN="your_token"

# Add friend (needed for notifications)
curl -X POST http://localhost:8000/add-friend \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Bob",
    "email":"bob@example.com",
    "notification_channel":"email"
  }'
# response: {"id":"...","name":"Bob","email":"bob@example.com",...}

# Send approval request
curl -X POST http://localhost:8000/send-approval \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
# response: {"id":"...","status":"pending","expires_at":"...","token":"..."}

# Extract token from response and approve via link
curl "http://localhost:8000/approve?token=THE_TOKEN"
# response: simple HTML page

# Or approve programmatically
curl -X POST http://localhost:8000/approve-access \
  -H "Content-Type: application/json" \
  -d '{"token":"THE_TOKEN","approver":"bob@example.com"}'
# response: {"status":"approved","unlock_minutes":5}
```

### Reporting
```bash
TOKEN="your_token"

# Get weekly report
curl -X GET http://localhost:8000/weekly-report \
  -H "Authorization: Bearer $TOKEN"
# response: {"user_id":"...","attempts":2,"most_attempted_website":"reddit.com","focus_score":99.5,"unique_domains":2}
```

## 3. Extension Testing (Manual)

### Build extension
```bash
cd extension
npm install
npm run build
# Confirm dist/*.js files exist and manifest.json references them
```

### Load in Chrome
1. Open `chrome://extensions`
2. Toggle Developer mode
3. Click Load unpacked
4. Select the repo `extension/` folder
5. Confirm FocusGuard appears and is enabled

### Test register/login
1. Open the extension popup
2. Enter email & password, click Register
3. Confirm status shows "Registered and token saved"
4. Refresh popup — token field should be pre-filled

### Test blocking
1. Popup: enter domain `youtube.com` and click Add
2. Open browser tab and navigate to `https://youtube.com`
3. Confirm tab redirects to `blocked.html` showing "Blocked by FocusGuard"
4. URL should show `blocked.html?domain=youtube.com`

### Test unlock request
1. From popup click "Request unlock"
2. Confirm status shows "Temporary unlock requested"
3. Navigate to `youtube.com` again — should no longer redirect (5 min window)
4. After 5 minutes, blocked again

### Test removal of blocked site
1. From popup, add a domain (e.g., `facebook.com`)
2. Manually edit extension storage to remove it (extension dev tools) or add removal UI button
3. Navigate to `facebook.com` — should load normally

## 4. Database Validation

### Connect to Postgres
```bash
# Using psql
psql "postgresql://postgres:postgres@localhost:5432/focusguard"

# Or Docker
docker exec -it <postgres_container> psql -U postgres -d focusguard
```

### Verify schema
```sql
-- List all tables
\dt

-- Inspect users table
\d users

-- Count records
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM blocked_sites;
SELECT COUNT(*) FROM block_attempts;
SELECT COUNT(*) FROM approval_requests;
```

### Query sample data
```sql
-- Recent block attempts
SELECT user_id, domain, attempted_at FROM block_attempts ORDER BY attempted_at DESC LIMIT 5;

-- User's blocked sites
SELECT domain, is_active FROM blocked_sites WHERE user_id = '<user_id>' ORDER BY created_at DESC;

-- Pending approvals
SELECT id, status, expires_at FROM approval_requests WHERE status = 'pending' ORDER BY created_at DESC LIMIT 3;
```

## 5. End-to-End Test Flow (Scripted)

Run this to exercise the entire system:

```bash
# 1. Start backend
docker compose up -d --build
sleep 5

# 2. Register & get token
TOKEN=$(curl -s -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"TestPass123!"}' | jq -r '.access_token')

echo "Token: $TOKEN"

# 3. Add friend
curl -s -X POST http://localhost:8000/add-friend \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Friend","email":"friend@example.com","notification_channel":"email"}' | jq .

# 4. Add blocked site
curl -s -X POST http://localhost:8000/add-blocked-site \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain":"youtube.com"}' | jq .

# 5. Log multiple attempts
for domain in "youtube.com" "reddit.com" "youtube.com"; do
  curl -s -X POST http://localhost:8000/log-attempt \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"domain\":\"$domain\",\"url\":\"https://$domain\",\"source\":\"extension\"}" | jq .
done

# 6. Get weekly report
curl -s -X GET http://localhost:8000/weekly-report \
  -H "Authorization: Bearer $TOKEN" | jq .

# 7. Send approval & approve
RESPONSE=$(curl -s -X POST http://localhost:8000/send-approval \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}')
echo "Approval response: $RESPONSE"

TOKEN_APPROVAL=$(echo $RESPONSE | jq -r '.token')
echo "Approval token: $TOKEN_APPROVAL"

curl -s -X POST http://localhost:8000/approve-access \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOKEN_APPROVAL\",\"approver\":\"friend@example.com\"}" | jq .

echo "✓ End-to-end test complete"
```

Save the above as `scripts/e2e-test.sh` and run:
```bash
bash scripts/e2e-test.sh
```

## 6. Extension Integration Testing (Advanced)

For automated extension testing, use Playwright or WebDriver:

```bash
# Install Playwright
npm install -D @playwright/test

# Run extension tests
npx playwright test extension/tests/
```

Test scenarios to cover:
- Register and token persistence
- Blocked site addition and local storage update
- Tab redirect when blocked domain visited
- Unlock expiry after 5 minutes
- Attempt logging POST to backend

(Test files can be added in `extension/tests/*.spec.ts` following Playwright patterns.)

## 7. Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend returns 401 | Check `Authorization: Bearer <token>` header; ensure token is valid via `/login` |
| Extension not redirecting | Confirm `dist/` build exists; check manifest `content_scripts` path |
| Postgres connection fails | Ensure DB URL is correct; check Postgres running: `docker compose ps` |
| Rate limit hit (429) | Wait 60 seconds or restart backend |
| Notification not sent | Ensure SendGrid/Twilio env vars set; check logs for errors |

## 8. Performance & Load Testing (Optional)

For stress testing, use `k6`:

```bash
npm install -g k6

# Create load test: k6/script.js
# Run test
k6 run k6/script.js
```

See `k6/script.js` for example load test that simulates concurrent block attempts.

---

**Next steps**: Run the manual curl tests first, then load the extension and verify the blocking flow. Then run the pytest suite for automated coverage.
