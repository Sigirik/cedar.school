# backend/scripts/db-import.ps1
<#
  Restores backend/db.sqlite3 from a snapshot (default: seeds/cedar_dev.sqlite3).
  Works from any directory (uses $PSScriptRoot). Can stop/start docker service and run migrations.
#>

[CmdletBinding()]
param(
  [string]$SnapshotPath = "seeds/cedar_dev.sqlite3",
  [switch]$Docker,
  [switch]$SkipMigrate
)

function Info($msg) { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Ok($msg)  { Write-Host "[ OK ]  $msg" -ForegroundColor Green }
function Warn($msg){ Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Err($msg) { Write-Host "[ERR ]  $msg" -ForegroundColor Red }

$ErrorActionPreference = "Stop"

try {
  # Script location: backend/scripts -> repo root two levels up
  $RepoRoot   = Resolve-Path (Join-Path $PSScriptRoot "..\..")
  $DbPath     = Join-Path $RepoRoot "backend\db.sqlite3"
  $BackendDir = Split-Path -Parent $DbPath

  # Resolve snapshot path to absolute
  if ([System.IO.Path]::IsPathRooted($SnapshotPath)) {
    $SnapshotAbs = $SnapshotPath
  } else {
    $SnapshotAbs = Join-Path $RepoRoot $SnapshotPath
  }

  if (!(Test-Path -Path $SnapshotAbs)) {
    throw "Snapshot not found: $SnapshotAbs"
  }

  if ($Docker) {
    Info "Stopping docker compose service 'backend'..."
    docker compose stop backend | Out-Null
    Ok "backend stopped"
  } else {
    Warn "Docker flag not set. If Django runserver is running, stop it before import."
  }

  if (!(Test-Path -Path $BackendDir)) {
    New-Item -ItemType Directory -Force -Path $BackendDir | Out-Null
    Ok "Created directory: $BackendDir"
  }

  Copy-Item -Path $SnapshotAbs -Destination $DbPath -Force
  Ok "Restored DB: $SnapshotAbs -> $DbPath"

  if ($Docker) {
    Info "Starting docker compose service 'backend'..."
    docker compose start backend | Out-Null
    Ok "backend started"

    if (-not $SkipMigrate) {
      Info "Running migrations inside container..."
      $migrated = $false
      try {
        docker compose exec backend bash -lc "python manage.py migrate --noinput"
        $migrated = $true
      } catch {
        Warn "First migrate attempt failed, retrying shortly..."
        Start-Sleep -Seconds 3
        docker compose exec backend bash -lc "python manage.py migrate --noinput"
        $migrated = $true
      }
      if ($migrated) { Ok "Migrations applied" }
    } else {
      Warn "SkipMigrate set: skipping migrations."
    }
  } else {
    if (-not $SkipMigrate) {
      Info "Run migrations locally:"
      Write-Host "  python manage.py migrate --noinput"
    } else {
      Warn "SkipMigrate set: skipping migrations."
    }
  }

  # Hash for reference
  $Hash = (Get-FileHash -Algorithm SHA256 -Path $DbPath).Hash
  Info "DB SHA256: $Hash"

  Write-Host ""
  Ok "Import finished."
}
catch {
  Err $_.Exception.Message
  exit 1
}
