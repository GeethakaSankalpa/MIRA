$ErrorActionPreference = "Stop"

Write-Host "== MIRA Dev Down =="

Set-Location "E:\MIRA\infra"
docker compose down

Write-Host "Done."