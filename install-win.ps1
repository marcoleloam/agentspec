# AgentSpec — Global Install for Windows
# Run with: powershell -ExecutionPolicy Bypass -File install-win.ps1

$AgentSpecDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClaudeDir = "$env:APPDATA\Claude"

Write-Host "AgentSpec — Global Install (Windows)"
Write-Host "======================================"
Write-Host "Source: $AgentSpecDir\.claude"
Write-Host "Target: $ClaudeDir"
Write-Host ""

# Create %APPDATA%\Claude if it doesn't exist
if (-not (Test-Path $ClaudeDir)) {
    New-Item -ItemType Directory -Path $ClaudeDir | Out-Null
}

# Helper: create or update a junction (Windows equivalent of symlink for dirs)
function Set-Junction {
    param($Link, $Target)

    $name = Split-Path -Leaf $Link

    if (Test-Path $Link) {
        $item = Get-Item $Link -Force
        if ($item.Attributes -match "ReparsePoint") {
            Write-Host "u  $name`: updating junction"
            Remove-Item $Link -Force -Recurse
        } else {
            Write-Host "!  $name`: directory already exists at $Link"
            Write-Host "   Remove it manually and re-run."
            return
        }
    } else {
        Write-Host "+  $name`: creating junction"
    }

    cmd /c mklink /J "$Link" "$Target" | Out-Null
}

# Junction for agents
Set-Junction "$ClaudeDir\agents" "$AgentSpecDir\.claude\agents"

# Junction for commands
Set-Junction "$ClaudeDir\commands" "$AgentSpecDir\.claude\commands"

# Copy settings.json only if not already present
$SettingsTarget = "$ClaudeDir\settings.json"
$SettingsSource = "$AgentSpecDir\.claude\settings.json"

if (Test-Path $SettingsTarget) {
    Write-Host "~  settings.json: already exists, skipping (not overwriting your config)"
} else {
    Write-Host "+  settings.json: copying permissions config"
    Copy-Item $SettingsSource $SettingsTarget
}

Write-Host ""
Write-Host "Done! AgentSpec v3.0.0 is now available globally."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Copy the project template to any new project:"
Write-Host "     Copy-Item $AgentSpecDir\CLAUDE.md.template C:\path\to\your-project\CLAUDE.md"
Write-Host ""
Write-Host "  2. Start using SDD commands in Claude Code:"
Write-Host "     /brainstorm, /define, /design, /build, /ship"
Write-Host ""
Write-Host "  To update AgentSpec later:"
Write-Host "     cd $AgentSpecDir && git pull"
Write-Host "     (junctions update automatically)"
