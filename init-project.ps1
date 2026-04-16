# ============================================================================
# AgentSpec — Project Setup (Windows PowerShell)
# Copies .claude/ into the target project for full functionality
# Usage: .\init-project.ps1 [target-dir]
# ============================================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path $ScriptDir ".claude"
$TargetBase = if ($args.Count -gt 0) { $args[0] } else { "." }
$Target = Join-Path $TargetBase ".claude"

if (-not (Test-Path $Source)) {
    Write-Host "ERROR: .claude/ not found at $Source" -ForegroundColor Red
    exit 1
}

$TargetAbs = (Resolve-Path $TargetBase).Path
Write-Host "AgentSpec — Project Setup"
Write-Host "========================="
Write-Host "Source: $Source"
Write-Host "Target: $TargetAbs\.claude"
Write-Host ""

# Remove old symlinks or directories (clean slate for shared content)
foreach ($dir in @("agents", "commands", "kb", "skills")) {
    $path = Join-Path $Target $dir
    if (Test-Path $path) {
        $item = Get-Item $path -Force
        if ($item.LinkType) {
            Write-Host "↻  Removing old symlink: $dir"
            Remove-Item $path -Force
        } else {
            Write-Host "↻  Removing old copy: $dir"
            Remove-Item $path -Recurse -Force
        }
    }
}

# Remove old SDD symlinks
foreach ($subdir in @("templates", "architecture")) {
    $path = Join-Path $Target "sdd\$subdir"
    if (Test-Path $path) {
        $item = Get-Item $path -Force
        if ($item.LinkType) {
            Write-Host "↻  Removing old symlink: sdd/$subdir"
            Remove-Item $path -Force
        } else {
            Remove-Item $path -Recurse -Force
        }
    }
}

# Create .claude/ if needed
New-Item -ItemType Directory -Path $Target -Force | Out-Null

# Copy shared content
foreach ($dir in @("agents", "commands", "kb", "skills")) {
    Copy-Item -Path (Join-Path $Source $dir) -Destination (Join-Path $Target $dir) -Recurse -Force
    Write-Host "→  Copied $dir/"
}

# SDD: copy templates + architecture, create local workspace
foreach ($subdir in @("features", "reports", "archive")) {
    New-Item -ItemType Directory -Path (Join-Path $Target "sdd\$subdir") -Force | Out-Null
}
Copy-Item -Path (Join-Path $Source "sdd\templates") -Destination (Join-Path $Target "sdd\templates") -Recurse -Force
Copy-Item -Path (Join-Path $Source "sdd\architecture") -Destination (Join-Path $Target "sdd\architecture") -Recurse -Force
Write-Host "→  Copied sdd/templates/"
Write-Host "→  Copied sdd/architecture/"

# Copy SDD index files
foreach ($f in @("_index.md", "README.md")) {
    $src = Join-Path $Source "sdd\$f"
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination (Join-Path $Target "sdd\$f") -Force
    }
}

# Summary
Write-Host ""
Write-Host "✅ Done!" -ForegroundColor Green
Write-Host ""
$AgentCount = (Get-ChildItem -Path (Join-Path $Target "agents") -Recurse -Filter "*.md" |
    Where-Object { $_.Name -ne "README.md" -and $_.Name -ne "_template.md" }).Count
$KbCount = (Get-ChildItem -Path (Join-Path $Target "kb") -Directory |
    Where-Object { $_.Name -ne "_templates" -and $_.Name -ne "shared" }).Count
Write-Host "  $AgentCount agents"
Write-Host "  $KbCount KB domains"
Write-Host "  5 SDD templates"
Write-Host ""
Write-Host "To update later: re-run this script (safe to repeat)"
Write-Host "  .\init-project.ps1 $TargetAbs"
