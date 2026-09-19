# CasePacket local E2E — API on :8000, Vite on :5173
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "== pip install ==" -ForegroundColor Cyan
python -m pip install -q -r local\requirements.txt

Write-Host "== starting API :8000 ==" -ForegroundColor Cyan
$api = Start-Process -PassThru -WindowStyle Minimized -FilePath "python" -ArgumentList @(
  "-m", "uvicorn", "local.server:app", "--host", "127.0.0.1", "--port", "8000"
) -WorkingDirectory $Root

Start-Sleep -Seconds 2
python scripts\smoke_e2e.py
if ($LASTEXITCODE -ne 0) {
  Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue
  exit $LASTEXITCODE
}

Write-Host "== frontend ==" -ForegroundColor Cyan
Set-Location "$Root\web"
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
if (-not (Test-Path node_modules)) { npm i }
npm run build
Write-Host "API PID $($api.Id) — open http://127.0.0.1:5173 after: npm run dev" -ForegroundColor Green
Write-Host "Stop API: Stop-Process -Id $($api.Id)" -ForegroundColor Yellow
