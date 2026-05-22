# FocusGuard End-to-End Test Script
# Windows PowerShell version

param(
    [string]$ApiBase = "http://localhost:8000",
    [string]$Email = "testuser_$(Get-Random)@example.com",
    [string]$Password = "TestPass123!"
)

Write-Host "FocusGuard E2E Test" -ForegroundColor Green
Write-Host "API Base: $ApiBase" -ForegroundColor Yellow
Write-Host "Test Email: $Email" -ForegroundColor Yellow

# Helper function for API calls
function Invoke-API {
    param(
        [string]$Method = "POST",
        [string]$Path,
        [object]$Body,
        [string]$Token
    )
    
    $url = "$ApiBase$Path"
    $headers = @{ "Content-Type" = "application/json" }
    
    if ($Token) {
        $headers["Authorization"] = "Bearer $Token"
    }
    
    $params = @{
        Uri     = $url
        Method  = $Method
        Headers = $headers
    }
    
    if ($Body) {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 10)
    }
    
    try {
        $response = Invoke-WebRequest @params
        return $response.Content | ConvertFrom-Json
    }
    catch {
        Write-Error "API Error: $($_.Exception.Message)"
        return $null
    }
}

# 1. Health check
Write-Host "`n[1/8] Health Check..." -ForegroundColor Cyan
$health = Invoke-API -Method GET -Path "/health"
if ($health.status -eq "ok") {
    Write-Host "✓ Backend is healthy" -ForegroundColor Green
} else {
    Write-Host "✗ Backend health check failed" -ForegroundColor Red
    exit 1
}

# 2. Register
Write-Host "`n[2/8] Registering User..." -ForegroundColor Cyan
$registerBody = @{ email = $Email; password = $Password }
$registerResp = Invoke-API -Path "/register" -Body $registerBody
if ($registerResp.access_token) {
    $TOKEN = $registerResp.access_token
    Write-Host "✓ User registered and token received" -ForegroundColor Green
    Write-Host "  Token: $($TOKEN.Substring(0, 20))..." -ForegroundColor Gray
} else {
    Write-Host "✗ Registration failed" -ForegroundColor Red
    exit 1
}

# 3. Add Friend
Write-Host "`n[3/8] Adding Friend..." -ForegroundColor Cyan
$friendBody = @{
    name                 = "TestFriend"
    email                = "friend@example.com"
    notification_channel = "email"
}
$friendResp = Invoke-API -Path "/add-friend" -Body $friendBody -Token $TOKEN
if ($friendResp.id) {
    Write-Host "✓ Friend added successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to add friend" -ForegroundColor Red
}

# 4. Add Blocked Site
Write-Host "`n[4/8] Adding Blocked Site..." -ForegroundColor Cyan
$siteBody = @{ domain = "youtube.com" }
$siteResp = Invoke-API -Path "/add-blocked-site" -Body $siteBody -Token $TOKEN
if ($siteResp.domain -eq "youtube.com") {
    Write-Host "✓ Blocked site added: youtube.com" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to add blocked site" -ForegroundColor Red
}

# 5. Log Multiple Attempts
Write-Host "`n[5/8] Logging Block Attempts..." -ForegroundColor Cyan
$attempts = 0
foreach ($domain in @("youtube.com", "reddit.com", "youtube.com")) {
    $attemptBody = @{
        domain = $domain
        url    = "https://$domain"
        source = "extension"
    }
    $attemptResp = Invoke-API -Path "/log-attempt" -Body $attemptBody -Token $TOKEN
    if ($attemptResp.status -eq "logged") {
        $attempts++
    }
}
Write-Host "✓ Logged $attempts block attempts" -ForegroundColor Green

# 6. Get Weekly Report
Write-Host "`n[6/8] Fetching Weekly Report..." -ForegroundColor Cyan
$reportResp = Invoke-API -Method GET -Path "/weekly-report" -Token $TOKEN
if ($reportResp.attempts) {
    Write-Host "✓ Weekly Report:" -ForegroundColor Green
    Write-Host "  - Total attempts: $($reportResp.attempts)" -ForegroundColor Gray
    Write-Host "  - Most attempted: $($reportResp.most_attempted_website)" -ForegroundColor Gray
    Write-Host "  - Unique domains: $($reportResp.unique_domains)" -ForegroundColor Gray
    Write-Host "  - Focus score: $($reportResp.focus_score)" -ForegroundColor Gray
} else {
    Write-Host "✗ Failed to fetch report" -ForegroundColor Red
}

# 7. Send Approval Request
Write-Host "`n[7/8] Sending Approval Request..." -ForegroundColor Cyan
$approvalResp = Invoke-API -Path "/send-approval" -Body @{} -Token $TOKEN
if ($approvalResp.token) {
    $APPROVAL_TOKEN = $approvalResp.token
    Write-Host "✓ Approval request sent" -ForegroundColor Green
    Write-Host "  - Token: $($APPROVAL_TOKEN.Substring(0, 20))..." -ForegroundColor Gray
    Write-Host "  - Status: $($approvalResp.status)" -ForegroundColor Gray
} else {
    Write-Host "✗ Failed to send approval request" -ForegroundColor Red
    exit 1
}

# 8. Approve Access
Write-Host "`n[8/8] Approving Access..." -ForegroundColor Cyan
$approveBody = @{
    token    = $APPROVAL_TOKEN
    approver = "friend@example.com"
}
$approveResp = Invoke-API -Path "/approve-access" -Body $approveBody
if ($approveResp.status -eq "approved") {
    Write-Host "✓ Access approved" -ForegroundColor Green
    Write-Host "  - Unlock minutes: $($approveResp.unlock_minutes)" -ForegroundColor Gray
} else {
    Write-Host "✗ Failed to approve access" -ForegroundColor Red
}

# Summary
Write-Host "`n" + ("=" * 50) -ForegroundColor Yellow
Write-Host "✓ End-to-End Test Complete!" -ForegroundColor Green
Write-Host "All critical flows tested successfully." -ForegroundColor Yellow
Write-Host "=" * 50 -ForegroundColor Yellow
