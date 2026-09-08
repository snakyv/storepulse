$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is not available. Start Docker Desktop first."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Write-Host "Starting five POS simulator instances..."
docker compose --profile demo up -d --build `
    simulator-madrid `
    simulator-london `
    simulator-new-york `
    simulator-tokyo `
    simulator-warsaw

Write-Host "Five POS simulators are running."
Write-Host "They emit SALE/REFUND traffic, late events and exact duplicate replays."
Write-Host "Tune per-store intensity and traffic rates in .env."
Write-Host "Frontend: http://localhost:5173"
docker compose --profile demo ps
