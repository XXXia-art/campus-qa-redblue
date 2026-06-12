# 本机红蓝队一体化代理启动脚本
# 一键启动：蓝队防御代理（下游） + 攻击者 MITM 代理（上游）
# 用法：.\start_redblue_chain.ps1 [-AttackMode prompt|mcp|both]

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

function Test-Mitmproxy {
    $cmd = Get-Command mitmweb -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Host "❌ mitmweb 命令未找到，请先激活 conda 环境或安装 mitmproxy：pip install mitmproxy" -ForegroundColor Red
        exit 1
    }
}

function Test-Port($port) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        $procIds = $conns | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $procIds) {
            $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($p) {
                Write-Host "⚠️ 端口 $port 被占用: $($p.ProcessName) (PID: $procId)" -ForegroundColor Yellow
            }
        }
        return $true
    }
    return $false
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  红蓝队一体化代理启动器（本机测试）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Test-Mitmproxy

# 检查端口占用
$ports = @($BlueListenPort, $BlueWebPort, $RedListenPort, $RedWebPort)
$occupied = $false
foreach ($p in $ports) {
    if (Test-Port $p) { $occupied = $true }
}
if ($occupied) {
    Write-Host ""
    Write-Host "❌ 请先释放以上端口，或修改启动参数使用其他端口。" -ForegroundColor Red
    exit 1
}

$root = $PSScriptRoot
$blueScript = Join-Path $root "mitm_blue_team.py"
$redScript = Join-Path $root "mitm_prompt_inject.py"

if (-not (Test-Path $blueScript)) {
    Write-Host "❌ 未找到蓝队脚本: $blueScript" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $redScript)) {
    Write-Host "❌ 未找到红队脚本: $redScript" -ForegroundColor Red
    exit 1
}

# 启动蓝队代理（下游，直接连互联网）
Write-Host "🛡️  启动蓝队防御代理..." -ForegroundColor Cyan
$blueCmd = "mitmweb --web-host 0.0.0.0 --web-port $BlueWebPort --listen-host 0.0.0.0 --listen-port $BlueListenPort --showhost --scripts `"$blueScript`""
$blueProc = Start-Process cmd -ArgumentList "/c", $blueCmd -PassThru -NoNewWindow
Write-Host "   蓝队代理 PID: $($blueProc.Id)  |  面板: http://localhost:$BlueWebPort" -ForegroundColor Green

Start-Sleep -Seconds 2

# 启动攻击者代理（上游指向蓝队代理）
Write-Host ""
Write-Host "🔴 启动攻击者 MITM 代理..." -ForegroundColor Cyan
$redCmdArgs = "--web-host 0.0.0.0 --web-port $RedWebPort --set web_password=mitm --listen-host 0.0.0.0 --listen-port $RedListenPort --showhost --mode upstream:http://127.0.0.1:$BlueListenPort --ssl-insecure"

if ($AttackMode -eq "prompt" -or $AttackMode -eq "both") {
    $redCmdArgs += " --scripts `"$redScript`""
}

$redCmd = "mitmweb $redCmdArgs"
$redProc = Start-Process cmd -ArgumentList "/c", $redCmd -PassThru -NoNewWindow
Write-Host "   红队代理 PID: $($redProc.Id)  |  面板: http://localhost:$RedWebPort" -ForegroundColor Green

Start-Sleep -Seconds 2

# 检查进程是否还在
if ($blueProc.HasExited) {
    Write-Host "❌ 蓝队代理启动失败" -ForegroundColor Red
    exit 1
}
if ($redProc.HasExited) {
    Write-Host "❌ 红队代理启动失败" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 红蓝队代理已启动" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "蓝队面板: http://localhost:$BlueWebPort" -ForegroundColor Yellow
Write-Host "红队面板: http://localhost:$RedWebPort  （密码: mitm）" -ForegroundColor Yellow
Write-Host ""
Write-Host "下一步：在第三个窗口启动 Streamlit" -ForegroundColor White
Write-Host "  cd A:\The_code\kimi_chat" -ForegroundColor Gray
Write-Host "  `$env:HTTP_PROXY=`"http://127.0.0.1:$RedListenPort`"" -ForegroundColor Gray
Write-Host "  `$env:HTTPS_PROXY=`"http://127.0.0.1:$RedListenPort`"" -ForegroundColor Gray
Write-Host "  streamlit run app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "关闭本窗口不会停止代理，需要时手动结束 PID $($blueProc.Id) 和 $($redProc.Id)" -ForegroundColor Gray
