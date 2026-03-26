param(
  [ValidateSet("minimal","full")]
  [string]$Mode = "minimal"
)

Set-Location $PSScriptRoot

# Activate virtual environment
. .\.venv\Scripts\Activate.ps1

if ($Mode -eq "minimal") {
    Write-Host "Running MINIMAL tests (matches CI minimal job)..."
    pytest -m "not integration" --tb=short
}
else {
    Write-Host "Running FULL test suite (matches CI full job)..."
    pytest --tb=short
}

exit $LASTEXITCODE