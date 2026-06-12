# MCP 协议安全攻防 — 攻击者电脑一键启动脚本（简化版）

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MCP 安全攻防实验室 — 攻击者控制台" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "建议以管理员身份运行" -ForegroundColor Yellow
}

# 获取热点IP
Write-Host "正在检测热点IP..." -ForegroundColor Green
$adapter = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -like "*Direct*" -or $_.InterfaceAlias -like "*Hotspot*" }
if ($adapter) {
    $hotspotIP = $adapter.IPAddress
    Write-Host "热点IP: $hotspotIP" -ForegroundColor Cyan
    Write-Host "参与者代理设置: $hotspotIP`:8080" -ForegroundColor Cyan
} else {
    $hotspotIP = Read-Host "请输入热点IP地址"
}

# 检查 mitmproxy
Write-Host ""
Write-Host "检查 mitmproxy..." -ForegroundColor Green
$mitmweb = Get-Command mitmweb -ErrorAction SilentlyContinue
if (-not $mitmweb) {
    Write-Host "mitmproxy 未安装，请先运行: pip install mitmproxy" -ForegroundColor Red
    exit
}
Write-Host "mitmproxy 已安装" -ForegroundColor Green

# 启动 mitmproxy
Write-Host ""
Write-Host "启动 mitmproxy..." -ForegroundColor Green
$proc = Start-Process mitmweb -ArgumentList "--web-host", "0.0.0.0", "--web-port", "8081", "--listen-host", "0.0.0.0", "--listen-port", "8080", "--showhost" -PassThru
Write-Host "mitmproxy 已启动 (PID: $($proc.Id))" -ForegroundColor Green

# 启动 Wireshark
Write-Host ""
Write-Host "启动 Wireshark..." -ForegroundColor Green
$ws1 = "C:\Program Files\Wireshark\Wireshark.exe"
$ws2 = "C:\Program Files (x86)\Wireshark\Wireshark.exe"
if (Test-Path $ws1) {
    Start-Process $ws1
    Write-Host "Wireshark 已启动" -ForegroundColor Green
} elseif (Test-Path $ws2) {
    Start-Process $ws2
    Write-Host "Wireshark 已启动" -ForegroundColor Green
} else {
    Write-Host "Wireshark 未找到，请手动启动" -ForegroundColor Yellow
}

# 打开浏览器
Write-Host ""
Write-Host "打开 mitmproxy Web 界面..." -ForegroundColor Green
Start-Process "http://localhost:8081"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "环境启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "参与者操作：" -ForegroundColor White
Write-Host "  1. 连接热点 MCP-Lab / seu2024." -ForegroundColor Gray
Write-Host "  2. 设置代理 $hotspotIP`:8080" -ForegroundColor Gray
Write-Host "  3. 安装证书 http://mitm.it" -ForegroundColor Gray
Write-Host "  4. 启动 Streamlit" -ForegroundColor Gray
Write-Host ""

Read-Host "按 Enter 停止 mitmproxy"

if ($proc) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "mitmproxy 已停止" -ForegroundColor Green
}

Write-Host "再见！" -ForegroundColor Green
