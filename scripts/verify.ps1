$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$ProjectRoot = (Get-Location).Path

function Run-Step([string]$Name, [scriptblock]$Command) {
    Write-Host ""
    Write-Host "=== $Name ==="
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

function Wait-ForPostgres {
    Write-Host ""
    Write-Host "=== Wait for PostgreSQL readiness ==="
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        docker compose exec -T postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "PostgreSQL is ready."
            return
        }
        Start-Sleep -Seconds 1
    }

    docker compose ps
    throw "PostgreSQL did not become ready within 30 seconds."
}

function Wait-ForBackend {
    Write-Host ""
    Write-Host "=== Wait for backend readiness ==="
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        try {
            $response = Invoke-RestMethod "http://localhost:8000/api/v1/health/ready" -TimeoutSec 2
            if ($response.status -eq "ready") {
                Write-Host "Backend is ready."
                return
            }
        }
        catch {
            # Retry while the container is starting.
        }
        Start-Sleep -Seconds 1
    }

    docker compose ps
    docker compose logs --tail=100 backend postgres
    throw "Backend did not become ready within 30 seconds."
}

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.12+ is required on the host for verification helpers."
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is not available. Start Docker Desktop first."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

if (-not (Test-Path "frontend/package-lock.json")) {
    throw "frontend/package-lock.json is required for reproducible npm ci installs."
}

Run-Step "Validate Compose configuration" { docker compose config -q }
Run-Step "Build current verification images" {
    docker compose build backend migrate seed frontend simulator-madrid
}
Run-Step "Start PostgreSQL" { docker compose up -d postgres }
Wait-ForPostgres
Run-Step "Apply migrations" { docker compose run --rm --no-deps migrate }
Run-Step "Seed deterministic demo data" { docker compose run --rm --no-deps seed }
Run-Step "Project Ruff" {
    docker compose run --rm --no-deps `
        --volume "${ProjectRoot}:/workspace:ro" `
        --workdir /workspace `
        backend `
        python scripts/run_ruff.py
}
Run-Step "Backend mypy" { docker compose run --rm --no-deps backend mypy app }
Run-Step "Backend pytest" { docker compose run --rm --no-deps backend python -m pytest -q }
Run-Step "Simulator compile" {
    docker compose run --rm --no-deps simulator-madrid python -m compileall -q simulator tests
}
Run-Step "Simulator unit tests" {
    docker compose run --rm --no-deps simulator-madrid `
        python -m unittest discover -s tests -v
}
Run-Step "Frontend dependency tree" {
    docker compose run --rm --no-deps frontend npm ls --depth=0
}
Run-Step "Frontend Node version" {
    docker compose run --rm --no-deps frontend node --version
}
Run-Step "Frontend npm version" {
    docker compose run --rm --no-deps frontend npm --version
}
Run-Step "Frontend TypeScript version" {
    docker compose run --rm --no-deps frontend ./node_modules/.bin/tsc --version
}
Run-Step "Frontend vue-tsc version" {
    docker compose run --rm --no-deps frontend ./node_modules/.bin/vue-tsc --version
}
Run-Step "Frontend typecheck" { docker compose run --rm --no-deps frontend npm run typecheck }
Run-Step "Frontend unit tests" { docker compose run --rm --no-deps frontend npm run test }
Run-Step "Frontend build" { docker compose run --rm --no-deps frontend npm run build }
Run-Step "Start backend for API smoke test" { docker compose up -d backend }
Wait-ForBackend

Write-Host ""
Write-Host "=== Seeded store API smoke test ==="
$stores = Invoke-RestMethod "http://localhost:8000/api/v1/stores" -TimeoutSec 5
if ($stores.Count -ne 5) {
    throw "Expected 5 seeded stores, got $($stores.Count)."
}
Write-Host "Seeded stores endpoint returned exactly 5 stores."

Run-Step "Verification helper unit tests" {
    python -m unittest discover -s scripts/tests -v
}
Run-Step "Five POS simulator traffic smoke" {
    python scripts/verify_simulator_smoke.py
}

Write-Host ""
Write-Host "Verification completed."
