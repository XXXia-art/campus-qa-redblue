# MCP 协议安全攻防 — 攻击者电脑一键启动脚本
# 以管理员身份运行 PowerShell，然后执行： .\start_attacker.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MCP 安全攻防实验室 — 攻击者控制台" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查管理员权限
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "⚠️ 警告：建议以管理员身份运行此脚本" -ForegroundColor Yellow
    Write-Host "   某些网络功能可能需要管理员权限" -ForegroundColor Yellow
    Write-Host ""
}

# ===== 1. 显示热点信息 =====
Write-Host "📶 步骤1：检查热点状态" -ForegroundColor Green

$hotspotAdapter = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.InterfaceAlias -like "*Direct*" -or 
    $_.InterfaceAlias -like "*Hotspot*" -or 
    $_.InterfaceAlias -like "*本地连接*" 
}

if ($hotspotAdapter) {
    $hotspotIP = $hotspotAdapter.IPAddress
    Write-Host "   ✅ 热点IP地址: $hotspotIP" -ForegroundColor Cyan
    Write-Host "   📢 告诉参与者设置代理: $hotspotIP`:8080" -ForegroundColor Cyan
} else {
    Write-Host "   ⚠️ 未检测到热点适配器" -ForegroundColor Yellow
    Write-Host "   请手动开启: 设置 → 网络和Internet → 移动热点" -ForegroundColor Yellow
    $hotspotIP = Read-Host "请输入热点IP地址(如 192.168.137.1)"
}

Write-Host ""

# ===== 2. 检查 mitmproxy =====
Write-Host "🔧 步骤2：检查 mitmproxy" -ForegroundColor Green

if (-not (Get-Command mitmweb -ErrorAction SilentlyContinue)) {
    Write-Host "   ❌ mitmproxy 未安装" -ForegroundColor Red
    Write-Host "   安装命令: pip install mitmproxy" -ForegroundColor Yellow
    exit
}

Write-Host "   ✅ mitmproxy 已安装" -ForegroundColor Green

# 检查证书
$certPath = "$env:USERPROFILE\.mitmproxy\mitmproxy-ca-cert.cer"
if (-not (Test-Path $certPath)) {
    Write-Host "   ⚠️ CA证书未生成，先启动一次mitmproxy..." -ForegroundColor Yellow
    Start-Process mitmweb -ArgumentList "--web-port", "18081" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Stop-Process -Name mitmweb -ErrorAction SilentlyContinue
}

Write-Host ""

# ===== 3. 启动 mitmproxy =====
Write-Host "🚀 步骤3：启动 mitmproxy" -ForegroundColor Green
Write-Host "   绑定地址: 0.0.0.0:8080 (允许局域网连接)" -ForegroundColor Gray
Write-Host "   Web界面: http://localhost:8081" -ForegroundColor Gray
Write-Host ""

$mitmProcess = Start-Process -FilePath "mitmweb" `
    -ArgumentList "--web-host", "0.0.0.0", "--web-port", "8081", "--listen-host", "0.0.0.0", "--listen-port", "8080", "--showhost" `
    -PassThru

Write-Host "   ✅ mitmproxy 已启动 (PID: $($mitmProcess.Id))" -ForegroundColor Green
Write-Host ""

# ===== 4. 启动 Wireshark =====
Write-Host "📡 步骤4：启动 Wireshark" -ForegroundColor Green

$wiresharkPath = "C:\Program Files\Wireshark\Wireshark.exe"
$wiresharkPath2 = "C:\Program Files (x86)\Wireshark\Wireshark.exe"

$actualWireshark = $null
if (Test-Path $wiresharkPath) {
    $actualWireshark = $wiresharkPath
} elseif (Test-Path $wiresharkPath2) {
    $actualWireshark = $wiresharkPath2
}

if ($actualWireshark) {
    Start-Process $actualWireshark
    Write-Host "   ✅ Wireshark 已启动" -ForegroundColor Green
    Write-Host "   💡 提示：选择热点网卡开始抓包" -ForegroundColor Yellow
} else {
    Write-Host "   ⚠️ Wireshark 未找到，请手动启动" -ForegroundColor Yellow
}

Write-Host ""

# ===== 5. 打开浏览器 =====
Write-Host "🌐 步骤5：打开 mitmproxy Web 界面" -ForegroundColor Green

Start-Process "http://localhost:8081"
Write-Host "   ✅ 浏览器已打开" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎉 攻击者环境启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 操作清单：" -ForegroundColor White
Write-Host "   1. 让参与者连接热点: MCP-Lab / seu2024." -ForegroundColor Gray
Write-Host "   2. 让参与者设置代理: $hotspotIP`:8080" -ForegroundColor Gray
Write-Host "   3. 让参与者安装证书: http://mitm.it" -ForegroundColor Gray
Write-Host "   4. 让参与者启动 Streamlit" -ForegroundColor Gray
Write-Host "   5. 在 mitmproxy 中拦截并篡改流量" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 攻击技巧：" -ForegroundColor White
Write-Host "   • 点击请求 → Intercept 暂停 → 修改 → Resume" -ForegroundColor Gray
Write-Host "   • 改请求URL: Nanjing → Beijing" -ForegroundColor Gray
Write-Host "   • 改响应JSON: temp_C 的值 +10" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️ 实验结束后：" -ForegroundColor Yellow
Write-Host "   按 Ctrl+C 关闭此窗口，停止 mitmproxy" -ForegroundColor Yellow
Write-Host ""

# 保持窗口打开
Write-Host "按 Enter 键停止所有服务并退出..." -ForegroundColor Cyan
Read-Host

# 清理
Write-Host ""
Write-Host "🧹 正在清理..." -ForegroundColor Yellow
if ($mitmProcess) {
    Stop-Process -Id $mitmProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "   mitmproxy 已停止" -ForegroundColor Green
}

Write-Host ""
Write-Host "👋 再见！" -ForegroundColor Green
