<#
.SYNOPSIS
  Runs the whole NAVY demo in containers (API + front end + CPU Qualifier) with one command.

.EXAMPLE
  .\flow\deploy\demo.ps1                      # build if needed, start, wait, open the browser
  .\flow\deploy\demo.ps1 -StopAirflow -Inject 6   # free Docker memory first, then send 6 dev tickets
  .\flow\deploy\demo.ps1 -Down                # stop the demo (state is kept)
  .\flow\deploy\demo.ps1 -Down -Reset         # stop it and erase the state volume

  OPENROUTER_API_KEY is read by Docker Compose from your shell or from .env; this script never
  reads or prints it. Everything runs locally and is free except the Drafter calls to OpenRouter.
#>
[CmdletBinding()]
param(
    [switch] $Down,            # stop the demo
    [switch] $Reset,           # with -Down: also delete the state volume (tickets, checkpoints)
    [switch] $StopAirflow,     # stop the l07-* Airflow containers first (they take the memory the Qualifier needs)
    [int] $Inject = 0,         # send this many dev tickets of the world through the API once it is ready
    [int] $Seed = 2,           # seed of the ticket selection
    [switch] $Rebuild,         # rebuild the images without cache
    [switch] $NoBrowser,
    [ValidateRange(1024, 65535)] [int] $Port = 8000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Compose = Join-Path $PSScriptRoot "compose.demo.yml"
$Model = Join-Path $ProjectRoot ".local\models\model-q4.gguf"
$World = Join-Path $ProjectRoot ".local\world\world.sqlite"
$Url = "http://127.0.0.1:8000"   # fixed by compose.demo.yml
Set-Location $ProjectRoot

function Step([string] $Message) { Write-Host "`n==> $Message" -ForegroundColor Cyan }
function Fail([string] $Message) { Write-Host "ERROR: $Message" -ForegroundColor Red; exit 1 }

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Fail "Docker is not installed or not on PATH." }
docker info *> $null
if ($LASTEXITCODE -ne 0) { Fail "Docker is not running. Start Docker Desktop and retry." }

if ($Down) {
    Step "Stopping the demo"
    $composeArgs = @("-f", $Compose, "down")
    if ($Reset) { $composeArgs += "-v" }
    docker compose @composeArgs
    exit $LASTEXITCODE
}

Step "Checking prerequisites"
if (-not (Test-Path $Model)) { Fail "Missing $Model. Run: uv run python -m flow.setup_local" }
if (-not (Test-Path $World)) {
    Write-Host "World database missing: building it (offline, free)..."
    uv run python -m flow.world.build --threads data/world/threads/accepted.jsonl
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $World)) { Fail "Could not build the world database." }
}

$airflow = @(docker ps --format "{{.Names}}" | Where-Object { $_ -like "l07-*" })
if ($airflow.Count -gt 0) {
    if ($StopAirflow) {
        Step "Stopping the Airflow containers ($($airflow.Count)); nothing is deleted"
        docker stop @airflow | Out-Null
    } else {
        Write-Host "WARNING: $($airflow.Count) l07 Airflow containers are running. Docker has little memory and the" -ForegroundColor Yellow
        Write-Host "         Qualifier needs about 2 GiB: it may be killed. Re-run with -StopAirflow to stop them." -ForegroundColor Yellow
    }
}

Step "Building and starting the containers"
if ($Rebuild) { docker compose -f $Compose build --no-cache; if ($LASTEXITCODE -ne 0) { Fail "Build failed." } }
docker compose -f $Compose up -d --build
if ($LASTEXITCODE -ne 0) { Fail "docker compose up failed. See: docker compose -f flow/deploy/compose.demo.yml logs" }

Step "Waiting for the flow to be ready (the Qualifier loads its model, about 40 s)"
$deadline = (Get-Date).AddMinutes(4)
$ready = $false
while ((Get-Date) -lt $deadline -and -not $ready) {
    try { $ready = (Invoke-WebRequest "$Url/health/ready" -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200 }
    catch { Start-Sleep -Seconds 3 }
}
if (-not $ready) {
    docker compose -f $Compose logs --tail 40
    Fail "The flow did not become ready. Most common causes: OPENROUTER_API_KEY missing, or the Qualifier ran out of memory."
}
Write-Host "Flow online: $Url" -ForegroundColor Green

if ($Inject -gt 0) {
    Step "Sending $Inject dev tickets of the world through the API"
    uv run python -m flow.inject_dataset --split val --world $World --limit $Inject --seed $Seed --api $Url --submit
}

if (-not $NoBrowser) { Start-Process $Url }
Write-Host "`nRunning. Stop with: .\flow\deploy\demo.ps1 -Down" -ForegroundColor Green
Write-Host "Logs: docker compose -f flow/deploy/compose.demo.yml logs -f"
