<#
One command for the presentation: API + front end on the world database, Qualifier on the Vertex
endpoint, demo panel enabled. Optionally resets the local state and pre-fills the history with fake
human reviewers (the demo-agent), so the dashboards and Langfuse show complete tickets.

  .\demo.ps1                          start only
  .\demo.ps1 -Reset -Prefill 80       back up and clear local state, then process 80 tickets
  .\demo.ps1 -Prefill 30 -Seed 8      add a fresh batch of 30 tickets
  .\demo.ps1 -Local -Prefill 30       Qualifier in local Docker (CPU, free) instead of Vertex

The fake reviewers use an LLM (OpenRouter, Drafter model) to write the human replies.
Without -Local, the Vertex endpoint must be deployed first (billed per hour; undeploy afterwards,
see docs/vertex_dq4_endpoint.md). Press Ctrl+C to stop the API, the front end and the reviewers.
#>
[CmdletBinding()]
param(
    [int] $Prefill = 0,
    [int] $Workers = 4,
    [int] $Seed = 7,
    [switch] $Reset,
    [switch] $NoBrowser,
    [switch] $Local,
    [string] $EndpointId = "7728645352521203712",
    [string] $WorldDb = ".local\world\world.sqlite"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:NAVY_DEMO_MODE = "1"
if (-not $Local) {
    $env:NAVY_QUALIFIER_PROVIDER = "vertex_raw_predict"
    $env:NAVY_QUALIFIER_VERTEX_ENDPOINT_ID = $EndpointId
    $env:GCP_PROJECT_ID = "agentics-workflows-2"
}

if ($Reset) {
    $backup = ".local\backup-flow-state-" + (Get-Date -Format "yyyyMMdd-HHmmss")
    New-Item -ItemType Directory -Path $backup | Out-Null
    Get-ChildItem ".local\flow" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "sqlite|\.db" } | Move-Item -Destination $backup
    Write-Host "Local flow state moved to $backup" -ForegroundColor Yellow
}

$reviewers = $null
if ($Prefill -gt 0) {
    New-Item -ItemType Directory -Force ".local\runs" | Out-Null
    $reviewers = Start-Job -ArgumentList $PSScriptRoot, $Prefill, $Seed, $Workers, $WorldDb -ScriptBlock {
        param($root, $count, $seed, $workers, $world)
        Set-Location $root
        for ($i = 0; $i -lt 120; $i++) {
            try { if ((Invoke-WebRequest "http://127.0.0.1:8000/health/ready" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { break } } catch { }
            Start-Sleep -Seconds 3
        }
        $env:PYTHONUNBUFFERED = "1"
        uv run python -m flow.demo_agent --limit $count --seed $seed --world $world --workers $workers --timeout 5400 --llm *> ".local\runs\demo-prefill.out"
    }
    Write-Host "Fake reviewers will process $Prefill tickets once the API is ready (log: .local\runs\demo-prefill.out)" -ForegroundColor Cyan
}

try {
    $options = @{ SkipQualifier = (-not $Local); SkipDependencyInstall = $true; WorldDb = $WorldDb }
    if ($NoBrowser) { $options.NoBrowser = $true }
    & .\run-local.ps1 @options
} finally {
    if ($null -ne $reviewers) { Stop-Job $reviewers -ErrorAction SilentlyContinue; Remove-Job $reviewers -Force -ErrorAction SilentlyContinue }
}
