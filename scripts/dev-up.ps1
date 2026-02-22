$ErrorActionPreference = "Stop"

Write-Host "== MIRA Dev Up =="

# Start Docker Desktop if it isn't running
if (-not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
  Write-Host "Starting Docker Desktop..."
  Start-Process "$Env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
}

# Wait for Docker Engine to be ready
Write-Host "Waiting for Docker engine..."
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
  try {
    docker info *> $null
    $ready = $true
    break
  } catch {
    Start-Sleep -Seconds 2
  }
}
if (-not $ready) { throw "Docker engine not ready after waiting." }

# Start infra
Set-Location "E:\MIRA\infra"
Write-Host "Starting infra containers..."
docker compose up -d

Write-Host "`nInfra status:"
docker compose ps

Write-Host "`nDone."