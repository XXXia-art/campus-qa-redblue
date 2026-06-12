# MCP Security Lab - Attacker Console
# Usage: .\start_attacker_en.ps1 [mcp|prompt|both]
#   mcp    - Standard transparent proxy for MCP attacks (default)
#   prompt - Inject malicious prompt into LLM API requests
#   both   - Enable both prompt injection and MCP proxy features

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("mcp", "prompt", "both")]
    [string]$Mode = "mcp",

    [Parameter(Mandatory=$false)]
    [string]$ListenPort = "8080",

    [Parameter(Mandatory=$false)]
    [string]$WebPort = "8081",

    # 网络层蓝队防御演示：将流量转发给下游蓝队代理，例如 127.0.0.1:8084
    [Parameter(Mandatory=$false)]
    [string]$UpstreamProxy = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MCP Security Lab - Attacker Console" -ForegroundColor Cyan
Write-Host "  Mode: $Mode" -ForegroundColor Yellow
Write-Host "  Proxy Port: $ListenPort" -ForegroundColor Yellow
Write-Host "  Web Port: $WebPort" -ForegroundColor Yellow
if ($UpstreamProxy) {
    Write-Host "  Upstream (Blue Team): $UpstreamProxy" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Warning: Run as administrator recommended" -ForegroundColor Yellow
}

# Get hotspot IP
Write-Host "Detecting hotspot IP..." -ForegroundColor Green

$adapter = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.IPAddress -like "192.168.137.*" -or 
    $_.InterfaceAlias -like "*Direct*" -or 
    $_.InterfaceAlias -like "*Hotspot*" -or 
    $_.InterfaceAlias -like "*Local Area Connection*"
}

if ($adapter) {
    $hotspotIP = $adapter.IPAddress
    Write-Host "Hotspot IP: $hotspotIP" -ForegroundColor Cyan
    Write-Host "Victim proxy: $hotspotIP`:$ListenPort" -ForegroundColor Cyan
} else {
    $hotspotIP = Read-Host "Enter hotspot IP (e.g. 192.168.137.1)"
}

# Check mitmproxy
Write-Host ""
Write-Host "Checking mitmproxy..." -ForegroundColor Green

$mitmweb = Get-Command mitmweb -ErrorAction SilentlyContinue
if (-not $mitmweb) {
    Write-Host "mitmproxy not found. Install: pip install mitmproxy" -ForegroundColor Red
    exit
}

Write-Host "mitmproxy found" -ForegroundColor Green

# Check script files for prompt injection mode
$scriptArgs = @()
if ($Mode -eq "prompt" -or $Mode -eq "both") {
    $promptScript = Join-Path $PSScriptRoot "mitm_prompt_inject.py"
    if (Test-Path $promptScript) {
        $scriptArgs += "--scripts"
        $scriptArgs += $promptScript
        Write-Host "Loaded prompt injection script: $promptScript" -ForegroundColor Green
    } else {
        Write-Host "Prompt injection script not found: $promptScript" -ForegroundColor Red
        exit
    }
}

# Check ports
function Test-PortOccupied($port) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        $procIds = $conns | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $procIds) {
            $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($p) {
                Write-Host "Port $port is occupied by: $($p.ProcessName) (PID: $procId)" -ForegroundColor Yellow
            }
        }
        return $true
    }
    return $false
}

$portListenBusy = Test-PortOccupied $ListenPort
$portWebBusy = Test-PortOccupied $WebPort
if ($portListenBusy -or $portWebBusy) {
    Write-Host "" 
    Write-Host "Please stop the processes above manually, or run this script as administrator." -ForegroundColor Red
    Write-Host "Alternatively, change the ports in this script and update victim proxy settings." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Start mitmproxy
Write-Host ""
Write-Host "Starting mitmproxy..." -ForegroundColor Green

# Create temp dir for logs
$tempDir = Join-Path $env:TEMP ("mitmweb-" + [System.Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

$logOut = Join-Path $tempDir "mitmweb.out.log"
$logErr = Join-Path $tempDir "mitmweb.err.log"

# Build command as a single string to avoid PowerShell argument parsing issues
$webPassword = "mitm"
$cmdArgs = "--web-host 0.0.0.0 --web-port $WebPort --set web_password=$webPassword --listen-host 0.0.0.0 --listen-port $ListenPort --showhost"
if ($UpstreamProxy) {
    # 转发到蓝队代理；--ssl-insecure 忽略上游自签证书（仅教学演示）
    $cmdArgs += " --mode upstream:http://$UpstreamProxy --ssl-insecure"
}
if ($scriptArgs.Count -gt 0) {
    $cmdArgs += " " + ($scriptArgs -join " ")
}
$cmd = "mitmweb $cmdArgs > `"$logOut`" 2> `"$logErr`""

try {
    $proc = Start-Process cmd -ArgumentList "/c", $cmd -PassThru -NoNewWindow -ErrorAction Stop
    Write-Host "mitmproxy starting (PID: $($proc.Id))" -ForegroundColor Green
} catch {
    Write-Host "Failed to start mitmproxy: $_" -ForegroundColor Red
    if ($tempDir -and (Test-Path $tempDir)) { Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue }
    exit 1
}

Write-Host "Log dir: $tempDir" -ForegroundColor Gray
Write-Host "Web UI password: $webPassword" -ForegroundColor Yellow

# Wait for mitmweb to start
Start-Sleep -Seconds 3

# Verify process is still running
if ($proc.HasExited) {
    Write-Host "mitmproxy exited unexpectedly!" -ForegroundColor Red
    Write-Host "=== stdout ===" -ForegroundColor Red
    if (Test-Path $logOut) { Get-Content $logOut | ForEach-Object { Write-Host $_ -ForegroundColor Red } }
    Write-Host "=== stderr ===" -ForegroundColor Red
    if (Test-Path $logErr) { Get-Content $logErr | ForEach-Object { Write-Host $_ -ForegroundColor Red } }
    if ($tempDir -and (Test-Path $tempDir)) { Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue }
    exit 1
}

# Try to extract token from log (fallback to fixed password)
$token = $webPassword
$logContent = ""
if (Test-Path $logOut) { $logContent += Get-Content $logOut -Raw -ErrorAction SilentlyContinue }
if (Test-Path $logErr) { $logContent += Get-Content $logErr -Raw -ErrorAction SilentlyContinue }

if ($logContent -match '\?token=([a-f0-9]{32})') {
    $token = $Matches[1]
    Write-Host "Detected random token: $token" -ForegroundColor Cyan
}

$webUrl = "http://127.0.0.1:$WebPort/?token=$token"
Write-Host "Web UI URL: $webUrl" -ForegroundColor Yellow
Start-Process $webUrl

if ($Mode -eq "prompt" -or $Mode -eq "both") {
    Write-Host ""
    Write-Host "Prompt injection active!" -ForegroundColor Red
    Write-Host "  Intercept filter: ~u api.xiaomimimo.com" -ForegroundColor Yellow
    Write-Host "  Or leave filter empty for automatic injection" -ForegroundColor Yellow
}

# Start Wireshark
Write-Host ""
Write-Host "Starting Wireshark..." -ForegroundColor Green

$ws1 = "D:\Wireshark\Wireshark.exe"
$ws2 = "C:\Program Files\Wireshark\Wireshark.exe"
$ws3 = "C:\Program Files (x86)\Wireshark\Wireshark.exe"

if (Test-Path $ws1) {
    Start-Process $ws1
    Write-Host "Wireshark started" -ForegroundColor Green
} elseif (Test-Path $ws2) {
    Start-Process $ws2
    Write-Host "Wireshark started" -ForegroundColor Green
} elseif (Test-Path $ws3) {
    Start-Process $ws3
    Write-Host "Wireshark started" -ForegroundColor Green
} else {
    Write-Host "Wireshark not found, start manually" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Victim steps:" -ForegroundColor White
Write-Host "  1. Connect to hotspot MCP-Lab / seu2024." -ForegroundColor Gray
Write-Host "  2. Set proxy to $hotspotIP`:8080" -ForegroundColor Gray
Write-Host "  3. Install cert from http://mitm.it" -ForegroundColor Gray
Write-Host "  4. Start Streamlit" -ForegroundColor Gray

if ($Mode -eq "prompt" -or $Mode -eq "both") {
    Write-Host ""
    Write-Host "Prompt Injection Demo:" -ForegroundColor White
    Write-Host "  1. Victim asks normal question in Campus QA page" -ForegroundColor Gray
    Write-Host "  2. Attacker modifies prompt via MITM" -ForegroundColor Gray
    Write-Host "  3. LLM response shows attack success" -ForegroundColor Gray
}

if ($Mode -eq "mcp" -or $Mode -eq "both") {
    Write-Host ""
    Write-Host "MCP MITM Demo:" -ForegroundColor White
    Write-Host "  1. Victim selects 'Malicious Proxy Attack' in MCP page" -ForegroundColor Gray
    Write-Host "  2. Set attack mode to tamper_request / tamper_response" -ForegroundColor Gray
    Write-Host "  3. Watch real API requests being modified" -ForegroundColor Gray
}

Write-Host ""

Read-Host "Press Enter to stop mitmproxy"

if ($proc) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "mitmproxy stopped" -ForegroundColor Green
}

# Cleanup temp config dir
if ($tempDir -and (Test-Path $tempDir)) {
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Cleaned up temp files" -ForegroundColor Green
}

Write-Host "Bye!" -ForegroundColor Green
