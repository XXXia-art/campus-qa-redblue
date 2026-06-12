# Local Red/Blue Team Proxy Chain Launcher
# Starts the blue-team defense proxy (downstream) and the red-team MITM proxy (upstream).
# Usage: .\start_redblue_chain.ps1 [-AttackMode prompt|mcp|both]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("mcp", "prompt", "both")]
    [string]$AttackMode = "prompt",

    [Parameter(Mandatory=$false)]
    [string]$BlueListenPort = "8084",

    [Parameter(Mandatory=$false)]
    [string]$BlueWebPort = "8085",

    [Parameter(Mandatory=$false)]
    [string]$RedListenPort = "8082",

    [Parameter(Mandatory=$false)]
    [string]$RedWebPort = "8083"
)

$ErrorActionPreference = "Stop"

function Test-MitmproxyInstalled {
    $cmd = Get-Command mitmweb -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Host "ERROR: mitmweb not found. Activate conda env or run: pip install mitmproxy" -ForegroundColor Red
        exit 1
    }
}

function Test-PortOccupied($port) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        $procIds = $conns | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $procIds) {
            $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($p) {
                Write-Host "WARNING: Port $port is occupied by $($p.ProcessName) (PID: $procId)" -ForegroundColor Yellow
            }
        }
        return $true
    }
    return $false
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Red/Blue Team Proxy Chain Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Test-MitmproxyInstalled

$ports = @($BlueListenPort, $BlueWebPort, $RedListenPort, $RedWebPort)
$occupied = $false
foreach ($p in $ports) {
    if (Test-PortOccupied $p) { $occupied = $true }
}
if ($occupied) {
    Write-Host ""
    Write-Host "ERROR: One or more ports are occupied. Free them or use different ports." -ForegroundColor Red
    exit 1
}

$root = $PSScriptRoot
$blueScript = Join-Path $root "mitm_blue_team.py"
$redScript = Join-Path $root "mitm_prompt_inject.py"

if (-not (Test-Path $blueScript)) {
    Write-Host "ERROR: Blue team script not found: $blueScript" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $redScript)) {
    Write-Host "ERROR: Red team script not found: $redScript" -ForegroundColor Red
    exit 1
}

# Start blue-team proxy (downstream, talks directly to the internet)
Write-Host "[*] Starting blue-team defense proxy..." -ForegroundColor Cyan
$blueCmd = "mitmweb --web-host 0.0.0.0 --web-port $BlueWebPort --listen-host 0.0.0.0 --listen-port $BlueListenPort --showhost --scripts `"$blueScript`""
$blueProc = Start-Process cmd -ArgumentList "/c", $blueCmd -PassThru -NoNewWindow
Write-Host "    Blue proxy PID: $($blueProc.Id)  Web UI: http://localhost:$BlueWebPort" -ForegroundColor Green

Start-Sleep -Seconds 2

# Start red-team MITM proxy (upstream points to blue-team proxy)
Write-Host ""
Write-Host "[*] Starting red-team MITM proxy..." -ForegroundColor Cyan
$redCmdArgs = "--web-host 0.0.0.0 --web-port $RedWebPort --set web_password=mitm --listen-host 0.0.0.0 --listen-port $RedListenPort --showhost --mode upstream:http://127.0.0.1:$BlueListenPort --ssl-insecure"

if ($AttackMode -eq "prompt" -or $AttackMode -eq "both") {
    $redCmdArgs += " --scripts `"$redScript`""
}

$redCmd = "mitmweb $redCmdArgs"
$redProc = Start-Process cmd -ArgumentList "/c", $redCmd -PassThru -NoNewWindow
Write-Host "    Red proxy PID: $($redProc.Id)  Web UI: http://localhost:$RedWebPort (password: mitm)" -ForegroundColor Green

Start-Sleep -Seconds 2

if ($blueProc.HasExited) {
    Write-Host "ERROR: Blue-team proxy exited unexpectedly." -ForegroundColor Red
    exit 1
}
if ($redProc.HasExited) {
    Write-Host "ERROR: Red-team proxy exited unexpectedly." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Red/Blue team proxies are running" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Blue web UI: http://localhost:$BlueWebPort" -ForegroundColor Yellow
Write-Host "Red  web UI: http://localhost:$RedWebPort (password: mitm)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next step: start Streamlit in a new window:" -ForegroundColor White
Write-Host "  cd A:\The_code\kimi_chat" -ForegroundColor Gray
Write-Host "  `$env:HTTP_PROXY=`"http://127.0.0.1:$RedListenPort`"" -ForegroundColor Gray
Write-Host "  `$env:HTTPS_PROXY=`"http://127.0.0.1:$RedListenPort`"" -ForegroundColor Gray
Write-Host "  streamlit run app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: closing this window will NOT stop the proxies." -ForegroundColor Gray
Write-Host "      Stop them manually with: Get-Process mitmweb | Stop-Process" -ForegroundColor Gray
