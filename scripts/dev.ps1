$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$env:CASEPACKET_LOCAL = "1"
$env:DEMO_API_KEY = "casepacket-demo-key"

Write-Host "Seeding fixtures..."
py scripts/seed.py

Write-Host "Starting API on :8080 (leave this window open)..."
Write-Host "In another terminal:  cd web; npm install; npm run dev"
Write-Host "Then open http://127.0.0.1:5173"
py scripts/local_server.py
