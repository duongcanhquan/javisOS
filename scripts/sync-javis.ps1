# Sync local Javis → GitHub → Ubuntu VPS (one command).
# Usage:
#   .\scripts\sync-javis.ps1
#   .\scripts\sync-javis.ps1 -Message "fix voice STT"
#   .\scripts\sync-javis.ps1 -SkipCommit   # chỉ push (nếu đã commit) + deploy VPS
param(
  [string]$Message = "Sync from Cursor",
  [string]$VpsHost = $(if ($env:JAVIS_VPS_HOST) { $env:JAVIS_VPS_HOST } else { "165.101.46.238" }),
  [string]$VpsUser = $(if ($env:JAVIS_VPS_USER) { $env:JAVIS_VPS_USER } else { "root" }),
  [string]$RemoteDir = $(if ($env:JAVIS_VPS_DIR) { $env:JAVIS_VPS_DIR } else { "/root/javis-os" }),
  [switch]$SkipCommit
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> Local repo: $Root" -ForegroundColor Cyan

if (-not $SkipCommit) {
  git add -A
  # Unstage local DBs / secrets if somehow staged
  git reset HEAD -- .env 2>$null
  git reset HEAD -- "server/*.db" "server/*.db-*" 2>$null
  $status = git status --porcelain
  if ($status) {
    git commit -m $Message
  } else {
    Write-Host "No local changes to commit." -ForegroundColor Yellow
  }
}

Write-Host "==> Push GitHub" -ForegroundColor Cyan
git push origin HEAD

$sshTarget = "${VpsUser}@${VpsHost}"
$identity = if ($env:JAVIS_VPS_KEY) { $env:JAVIS_VPS_KEY } else { Join-Path $env:USERPROFILE ".ssh\javis_vps_ed25519" }
$remoteCmd = "cd $RemoteDir && export COMPOSE_PROJECT_NAME=javis && bash scripts/vps-deploy.sh"
Write-Host "==> Deploy VPS: $sshTarget → $RemoteDir" -ForegroundColor Cyan
ssh -i $identity -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new $sshTarget $remoteCmd

Write-Host "==> Sync done (GitHub + Ubuntu)." -ForegroundColor Green
