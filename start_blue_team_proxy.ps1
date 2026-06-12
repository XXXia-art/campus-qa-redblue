# 蓝队网络层防御代理
# 部署在攻击者代理下游，用于检测/清洗 MITM 注入的 prompt。
# 本机测试默认监听 8084，Web 面板 8085。

param(
    [Parameter(Mandatory=$false)]
    [string]$ListenPort = "8084",

    [Parameter(Mandatory=$false)]
    [string]$WebPort = "8085"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Blue Team Network Defense Proxy" -ForegroundColor Cyan
Write-Host "  Listen: 127.0.0.1:$ListenPort" -ForegroundColor Yellow
Write-Host "  Web UI: 127.0.0.1:$WebPort" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$mitmweb = Get-Command mitmweb -ErrorAction SilentlyContinue
if (-not $mitmweb) {
    Write-Host "mitmproxy not found. Install: pip install mitmproxy" -ForegroundColor Red
    exit
}

$script = Join-Path $PSScriptRoot "mitm_blue_team.py"
if (-not (Test-Path $script)) {
    Write-Host "Blue team script not found: $script" -ForegroundColor Red
    exit
}

$cmd = "mitmweb --web-host 0.0.0.0 --web-port $WebPort --listen-host 0.0.0.0 --listen-port $ListenPort --showhost --scripts `"$script`""

$proc = Start-Process cmd -ArgumentList "/c", $cmd -PassThru -NoNewWindow
Write-Host "Blue team proxy started (PID: $($proc.Id))" -ForegroundColor Green
Write-Host "Web UI: http://localhost:$WebPort" -ForegroundColor Yellow
Write-Host ""
Write-Host "Victim proxy should still point to the attacker proxy." -ForegroundColor Gray
Write-Host "Attacker proxy should upstream to this blue proxy when demonstrating network defense." -ForegroundColor Gray
