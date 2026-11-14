[CmdletBinding()]
param(
    [ValidateRange(1024, 65535)] [int] $ApiPort = 8000,
    [ValidateRange(1024, 65535)] [int] $FrontendPort = 5173,
    [switch] $SkipQualifier,
    [switch] $DownloadModel,
    [switch] $SkipDependencyInstall,
    [switch] $NoBrowser,
    [string] $WorldDb = ""   # path of a world database (flow\world build) to show merchants and conversations
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$FrontendRoot = Join-Path $ProjectRoot "frontend"
$LocalRoot = Join-Path $ProjectRoot ".local"
$LogRoot = Join-Path $LocalRoot "logs"
$ApiProcess = $null
$FrontendProcess = $null
$QualifierStarted = $false
$ComposeFile = Join-Path $ProjectRoot "flow\docker-compose.yml"
$ModelFile = Join-Path $LocalRoot "models\model-q4.gguf"

function Write-Step([string] $Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-HttpReady([string] $Uri, [int] $TimeoutSeconds, [System.Diagnostics.Process] $Process) {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($null -ne $Process) {
            $Process.Refresh()
            if ($Process.HasExited) { return $false }
        }
        try {
            $response = Invoke-WebRequest -Uri $Uri -TimeoutSec 2 -UseBasicParsing
            if ($response.StatusCode -eq 200) { return $true }
        } catch { }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Stop-LocalProcess([System.Diagnostics.Process] $Process, [string] $Name) {
    if ($null -eq $Process) { return }
    $Process.Refresh()
    if (-not $Process.HasExited) {
        Write-Host "Stopping $Name (PID $($Process.Id))…"
        $taskkill = Get-Command taskkill.exe -ErrorAction SilentlyContinue
        if ($null -ne $taskkill) { & $taskkill.Source /PID $Process.Id /T /F *> $null }
        else { Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue }
        try { $Process.WaitForExit(5000) | Out-Null } catch { }
    }
}

function Assert-PortAvailable([int] $Port) {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    try { $listener.Start() }
    catch { throw "Port $Port is already in use. Stop its service or choose another port." }
    finally { $listener.Stop() }
}

Push-Location $ProjectRoot
try {
    if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
        Copy-Item (Join-Path $ProjectRoot ".env.example") (Join-Path $ProjectRoot ".env")
        throw "A .env file was created from .env.example. Add OPENROUTER_API_KEY to it, then run this script again. Langfuse keys are optional."
    }

    $hasOpenRouterKey = $false
    foreach ($line in [System.IO.File]::ReadAllLines((Join-Path $ProjectRoot ".env"))) {
        if ($line -match '^\s*OPENROUTER_API_KEY\s*=\s*(.*?)\s*$') {
            $candidate = $Matches[1].Trim('"').Trim("'")
            if ($candidate -and $candidate -notmatch '^your[-_ ]') { $hasOpenRouterKey = $true }
            $candidate = $null
            break
        }
    }
    if (-not $hasOpenRouterKey) { throw "OPENROUTER_API_KEY is missing or still has its example value in .env. The API requires it for Drafter requests." }
    if ($ApiPort -eq $FrontendPort) { throw "API and frontend must use different ports." }

    $Uv = Join-Path $LocalRoot "uv-bin\bin\uv.exe"
    if (-not (Test-Path $Uv)) {
        $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
        if ($null -eq $uvCommand) { throw "uv was not found. Install uv or place it at .local\uv-bin\bin\uv.exe." }
        $Uv = $uvCommand.Source
    }
    $NodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($null -eq $NodeCommand) { throw "Node.js 20.19+ is required for the Vite frontend." }
    $Node = $NodeCommand.Source
    $nodeVersionText = (& $Node --version).TrimStart('v')
    $nodeVersion = [version]$nodeVersionText
    if (-not (($nodeVersion.Major -eq 20 -and $nodeVersion.Minor -ge 19) -or ($nodeVersion.Major -ge 22 -and ($nodeVersion.Major -gt 22 -or $nodeVersion.Minor -ge 12)))) {
        throw "Node.js 20.19+ or 22.12+ is required; found v$nodeVersionText."
    }

    $Python3116 = Join-Path $LocalRoot "python\cpython-3.11.6-windows-x86_64-none\python.exe"
    $UvPythonArgs = @()
    if (Test-Path $Python3116) { $UvPythonArgs = @("--python", $Python3116) }

    if (-not $SkipDependencyInstall) {
        Write-Step "Syncing the locked Python environment"
        & $Uv sync --locked @UvPythonArgs
        if ($LASTEXITCODE -ne 0) { throw "uv sync failed with exit code $LASTEXITCODE." }

        if (-not (Test-Path (Join-Path $FrontendRoot "node_modules"))) {
            Write-Step "Installing locked frontend dependencies"
            Push-Location $FrontendRoot
            try {
                & npm.cmd ci
                if ($LASTEXITCODE -ne 0) { throw "npm ci failed with exit code $LASTEXITCODE." }
            } finally { Pop-Location }
        }
    }

    if (-not (Test-Path (Join-Path $FrontendRoot "node_modules\vite\bin\vite.js"))) {
        throw "Frontend dependencies are missing. Run npm ci in frontend or rerun without -SkipDependencyInstall."
    }
    New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"

    if (-not $SkipQualifier) {
        if (-not (Test-Path $ModelFile)) {
            if (-not $DownloadModel) {
                $answer = Read-Host "The local Qualifier model (~2 GB) is missing. Download it from the configured GCS bucket using your Google ADC credentials? [y/N]"
                $DownloadModel = $answer -match '^(y|yes)$'
            }
            if (-not $DownloadModel) { throw "The model is required. Run with -DownloadModel (requires GCP access) or -SkipQualifier for UI/API development without local inference." }
            Write-Step "Downloading and checksum-verifying the Qualifier model (about 2 GB)"
            & $Uv run --locked @UvPythonArgs python -m flow.setup_local
            if ($LASTEXITCODE -ne 0) { throw "Model setup failed. Check Google Application Default Credentials and GCS access." }
        }

        $DockerCommand = Get-Command docker.exe -ErrorAction SilentlyContinue
        if ($null -eq $DockerCommand) { throw "Docker Desktop with Docker Compose v2 is required. Start Docker Desktop or use -SkipQualifier for UI/API development." }
        & $DockerCommand.Source info *> $null
        if ($LASTEXITCODE -ne 0) { throw "Docker is installed but its engine is not ready. Start Docker Desktop and retry." }

        Write-Step "Starting the local Qualifier model (CPU, Docker)"
        $QualifierStarted = $true
        & $DockerCommand.Source compose -f $ComposeFile up -d
        if ($LASTEXITCODE -ne 0) { throw "Docker Compose could not start the Qualifier." }
        if (-not (Test-HttpReady "http://127.0.0.1:8081/health" 180 $null)) {
            throw "The Qualifier did not become ready within 3 minutes. Inspect Docker logs with: docker compose -f flow/docker-compose.yml logs qualifier"
        }
    }

    Write-Step "Starting the local Flow API"
    if ($WorldDb) { $env:NAVY_WORLD_DB = (Resolve-Path $WorldDb).Path }
    Assert-PortAvailable $ApiPort
    $apiOut = Join-Path $LogRoot "api-$stamp.out.log"
    $apiErr = Join-Path $LogRoot "api-$stamp.err.log"
    $apiArgs = @("run", "--locked") + $UvPythonArgs + @("uvicorn", "flow.api:app", "--host", "127.0.0.1", "--port", [string]$ApiPort)
    $ApiProcess = Start-Process -FilePath $Uv -ArgumentList $apiArgs -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $apiOut -RedirectStandardError $apiErr -PassThru
    if (-not (Test-HttpReady "http://127.0.0.1:$ApiPort/health/ready" 90 $ApiProcess)) {
        if (Test-Path $apiErr) { Get-Content $apiErr -Tail 35 }
        throw "The Flow API failed to become ready. Logs are in .local\logs."
    }

    Write-Step "Starting the frontend"
    Assert-PortAvailable $FrontendPort
    $frontendOut = Join-Path $LogRoot "frontend-$stamp.out.log"
    $frontendErr = Join-Path $LogRoot "frontend-$stamp.err.log"
    $viteCli = Join-Path $FrontendRoot "node_modules\vite\bin\vite.js"
    $FrontendProcess = Start-Process -FilePath $Node -ArgumentList @($viteCli, "--host", "127.0.0.1", "--port", [string]$FrontendPort, "--strictPort") -WorkingDirectory $FrontendRoot -WindowStyle Hidden -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr -PassThru
    $frontendUri = "http://127.0.0.1:$FrontendPort/"
    if (-not (Test-HttpReady $frontendUri 30 $FrontendProcess)) {
        if (Test-Path $frontendErr) { Get-Content $frontendErr -Tail 35 }
        throw "The frontend failed to become ready. Logs are in .local\logs."
    }

    Write-Host "`nLocal Keelpay flow is running:" -ForegroundColor Green
    Write-Host "  Frontend: $frontendUri"
    Write-Host "  API docs: http://127.0.0.1:$ApiPort/docs"
    if ($SkipQualifier) { Write-Host "  Qualifier: skipped (inference will be unavailable)" -ForegroundColor Yellow }
    Write-Host "  Logs:     .local\logs\*-$stamp.*.log"
    Write-Host "Press Ctrl+C to stop the API, frontend, and Qualifier container."
    if (-not $NoBrowser) { Start-Process $frontendUri }

    while ($true) {
        Start-Sleep -Seconds 1
        $ApiProcess.Refresh()
        $FrontendProcess.Refresh()
        if ($ApiProcess.HasExited) {
            if (Test-Path $apiErr) { Get-Content $apiErr -Tail 35 }
            throw "The Flow API stopped unexpectedly."
        }
        if ($FrontendProcess.HasExited) {
            if (Test-Path $frontendErr) { Get-Content $frontendErr -Tail 35 }
            throw "The frontend stopped unexpectedly."
        }
    }
} finally {
    Stop-LocalProcess $FrontendProcess "frontend"
    Stop-LocalProcess $ApiProcess "Flow API"
    if ($QualifierStarted) {
        $dockerForCleanup = Get-Command docker.exe -ErrorAction SilentlyContinue
        if ($null -ne $dockerForCleanup) {
            Write-Host "Stopping the local Qualifier container…"
            & $dockerForCleanup.Source compose -f $ComposeFile down
        }
    }
    Pop-Location
}
