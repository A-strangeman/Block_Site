# Run all tests for FocusGuard

param(
    [switch]$Coverage,
    [switch]$Verbose,
    [string]$Marker = ""
)

Write-Host "Running FocusGuard Tests..." -ForegroundColor Green

# Ensure pytest is installed
Write-Host "Checking pytest installation..." -ForegroundColor Yellow
pip install pytest pytest-asyncio aiosqlite -q

# Build pytest command
$testCmd = "pytest"
$testArgs = @("backend/tests", "-v")

if ($Verbose) {
    $testArgs += @("-vv", "-s")
}

if ($Coverage) {
    $testArgs += @("--cov=app", "--cov-report=html", "--cov-report=term")
}

if ($Marker) {
    $testArgs += @("-m", $Marker)
}

# Run tests
Write-Host "Running: $testCmd $($testArgs -join ' ')" -ForegroundColor Cyan
& $testCmd @testArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ All tests passed!" -ForegroundColor Green
    if ($Coverage) {
        Write-Host "Coverage report: htmlcov/index.html" -ForegroundColor Gray
    }
} else {
    Write-Host "`n✗ Some tests failed" -ForegroundColor Red
    exit 1
}
