$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is not available. Start Docker Desktop first."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Write-Host "Starting five heartbeat simulator instances..."
docker compose --profile demo up -d --build `
    simulator-madrid `
    simulator-london `
    simulator-new-york `
    simulator-tokyo `
    simulator-warsaw

Write-Host "Five simulators are running. Open http://localhost:5173 in one or two tabs."
docker compose --profile demo ps
