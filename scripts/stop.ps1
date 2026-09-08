$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
Write-Host "Stopping StorePulse services while preserving PostgreSQL data..."
docker compose --profile demo stop
