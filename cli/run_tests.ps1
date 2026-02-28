# 测试脚本与验证：覆盖 gateway->server 改动，确保无错误
# 用法：在 cli 目录下执行 .\run_tests.ps1 或 pwsh run_tests.ps1

$ErrorActionPreference = "Stop"
$cliRoot = $PSScriptRoot

Write-Host "=== 1. Python 单元测试 (pytest) ===" -ForegroundColor Cyan
Set-Location $cliRoot
pytest tests/ -v --tb=short 2>&1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== 2. Node server 单元测试 (可选) ===" -ForegroundColor Cyan
$serverDir = Join-Path $cliRoot "joytrunk\server"
if (Test-Path (Join-Path $serverDir "tests\api.test.js")) {
    Set-Location $serverDir
    node --test tests/*.js 2>&1
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "跳过（未找到 server/tests）" -ForegroundColor Yellow
}

Write-Host "`n=== 3. Smoke: joytrunk status（需已 onboard） ===" -ForegroundColor Cyan
Set-Location $cliRoot
$env:JOYTRUNK_ROOT = [System.IO.Path]::GetTempPath() + "joytrunk_smoke_" + [guid]::NewGuid().ToString("N").Substring(0,8)
New-Item -ItemType Directory -Path $env:JOYTRUNK_ROOT -Force | Out-Null
# 写入最小 config，使 get_base_url 可测
$config = @{ version = 1; server = @{ host = "127.0.0.1"; port = 32890 } } | ConvertTo-Json -Depth 3
Set-Content -Path (Join-Path $env:JOYTRUNK_ROOT "config.json") -Value $config -Encoding UTF8
joytrunk status 2>&1
$statusExit = $LASTEXITCODE
Remove-Item -Path $env:JOYTRUNK_ROOT -Recurse -Force -ErrorAction SilentlyContinue
if ($statusExit -ne 0) {
    Write-Host "joytrunk status 退出码 $statusExit（若本机未启动 server 属正常）" -ForegroundColor Yellow
}

Write-Host "`n=== 全部检查完成 ===" -ForegroundColor Green
