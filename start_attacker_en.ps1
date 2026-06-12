# MCP Security Lab - Attacker Console (English version for stability)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MCP Security Lab - Attacker Console" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Warning: Run as administrator recommended" -ForegroundColor Yellow
}

# Get hotspot IP
Write-Host "Detecting hotspot IP..." -ForegroundColor Green
$adapter = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -like "*Direct*" -or $_.InterfaceAlias -like "*Hotspot*" }
if ($adapter) {
    $hotspotIP = $adapter.IPAddress
    Write-Host "Hotspot IP: $hotspotIP" -ForegroundColor Cyan
    Write-Host "Victim proxy: $hotspotIP`:8080" -ForegroundColor Cyan
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

# Start mitmproxy
Write-Host ""
Write-Host "Starting mitmproxy..." -ForegroundColor Green
$proc = Start-Process mitmweb -ArgumentList "--web-host", "0.0.0.0", "--web-port", "8081", "--listen-host", "0.0.0.0", "--listen-port", "8080", "--showhost" -PassThru
Write-Host "mitmproxy started (PID: $($proc.Id))" -ForegroundColor Green

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

# Open browser
Write-Host ""
Write-Host "Opening mitmproxy web UI..." -ForegroundColor Green
Start-Process "http://localhost:8081"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Victim steps:" -ForegroundColor White
Write-Host "  1. Connect to hotspot MCP-Lab / seu2024" -ForegroundColor Gray
Write-Host "  2. Set proxy to $hotspotIP`:8080" -ForegroundColor Gray
Write-Host "  3. Install cert from http://mitm.it" -ForegroundColor Gray
Write-Host "  4. Start Streamlit" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to stop mitmproxy"

if ($proc) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "mitmproxy stopped" -ForegroundColor Green
}

Write-Host "Bye!" -ForegroundColor Green
