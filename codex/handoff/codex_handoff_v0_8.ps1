# ════════════════════════════════════════════════════════════════════════
# 📦 Codex Handoff Protocol v0.8
# Author: James Paul Jackson
# Role: Packages Codex state and prepares AI-to-AI continuity handoff
# ════════════════════════════════════════════════════════════════════════

param(
    [string]$StateFile = "C:\\Users\\jacks\\OneDrive\\Desktop\\Codex Web\\codex\\handoff\\handoff_state.json"
)

$CodexRoot = "C:\\Users\\jacks\\OneDrive\\Desktop\\Codex Web"
$LogDir    = Join-Path $CodexRoot "codex\\handoff\\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

$Stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$LogFile = Join-Path $LogDir "handoff_log_v0_8_$Stamp.txt"
$Payload = [ordered]@{
    version = "0.8"
    created = (Get-Date).ToString("s")
    author  = "James Paul Jackson"
    purpose = "Codex Reflective State Handoff"
    root    = $CodexRoot
    memory  = "Codex Memory Core v1.2"
}

$Payload | ConvertTo-Json -Depth 4 | Out-File $StateFile -Encoding utf8
"🧠 Handoff state written → $StateFile" | Tee-Object -FilePath $LogFile

Set-Location $CodexRoot
Write-Host "✅ Codex Handoff Protocol v0.8 complete."
