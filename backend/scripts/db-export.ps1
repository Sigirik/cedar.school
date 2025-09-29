# scripts/db-export.ps1
<#
.SYNOPSIS
  Делает снапшот локальной БД SQLite из backend/db.sqlite3 в seeds/cedar_dev.sqlite3 (или в путь по выбору).

.PARAMETER SnapshotPath
  Путь к файлу снапшота (по умолчанию: seeds/cedar_dev.sqlite3)

.PARAMETER Docker
  Остановить/запустить сервис backend через docker compose, чтобы гарантированно скопировать незалоченный файл.

.EXAMPLE
  .\scripts\db-export.ps1
  # экспорт без Docker (убедись, что runserver остановлен)

.EXAMPLE
  .\scripts\db-export.ps1 -Docker
  # экспорт c остановкой/запуском docker compose сервиса "backend"
#>

[CmdletBinding()]
param(
  [string]$SnapshotPath = "seeds/cedar_dev.sqlite3",
  [switch]$Docker
)

function Info($msg) { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "[ OK ]  $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Err($msg)  { Write-Host "[ERR ]  $msg" -ForegroundColor Red }

$ErrorActionPreference = "Stop"

try {
  # Script is in backend/scripts -> repo root is two levels up
  $RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
  $DbPath   = Join-Path $RepoRoot "backend\db.sqlite3"

  if (!(Test-Path -Path $DbPath)) {
    throw "DB file not found: $DbPath. Run migrations to create it."
  }

  if ($Docker) {
    Info "Stopping docker compose service 'backend'..."
    docker compose stop backend | Out-Null
    Ok "backend stopped"
  } else {
    Warn "Docker flag not set. If Django runserver is running, stop it before export."
  }

  # Normalize snapshot path to absolute (relative to repo root if needed)
  if ([System.IO.Path]::IsPathRooted($SnapshotPath)) {
    $SnapshotAbs = $SnapshotPath
  } else {
    $SnapshotAbs = Join-Path $RepoRoot $SnapshotPath
  }

  $SnapshotDir = Split-Path -Parent $SnapshotAbs
  if (![string]::IsNullOrWhiteSpace($SnapshotDir) -and !(Test-Path -Path $SnapshotDir)) {
    New-Item -ItemType Directory -Force -Path $SnapshotDir | Out-Null
    Ok "Created directory: $SnapshotDir"
  }

  Copy-Item -Path $DbPath -Destination $SnapshotAbs -Force
  Ok "Snapshot written: $SnapshotAbs"

  if (Test-Path -Path $SnapshotAbs) {
    $Hash = (Get-FileHash -Algorithm SHA256 -Path $SnapshotAbs).Hash
    Info "SHA256: $Hash"
  }

  if ($Docker) {
    Info "Starting docker compose service 'backend'..."
    docker compose start backend | Out-Null
    Ok "backend started"
  }

  Write-Host ""
  Ok "Export finished."
  Info "Next steps:"
  Write-Host "  git add $SnapshotPath"
  Write-Host '  git commit -m "chore(seed): refresh sqlite snapshot"'
}
catch {
  Err $_.Exception.Message
  exit 1
}