$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "Checking Docker Desktop..."
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is not available. Start Docker Desktop and run this script again."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host "Building and starting StorePulse foundation..."
docker compose up -d --build postgres migrate seed backend frontend

Write-Host "Waiting for backend readiness..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-RestMethod "http://localhost:8000/api/v1/health/ready" -TimeoutSec 2
        if ($response.status -eq "ready") {
            $ready = $true
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $ready) {
    docker compose ps
    throw "Backend did not become ready. Inspect: docker compose logs backend postgres migrate seed"
}

Write-Host ""
Write-Host "StorePulse foundation is ready."
Write-Host "Frontend: http://localhost:5173"
Write-Host "Swagger:  http://localhost:8000/docs"
Write-Host ""
docker compose ps
