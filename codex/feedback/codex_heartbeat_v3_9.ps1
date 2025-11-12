<#
╔══════════════════════════════════════════════════════════════════════════════════════╗
║ 💓  Codex Heartbeat v3.9 — Temporal Awareness Node (PS5-safe)                        ║
║ Author  : James Paul Jackson                                                         ║
║ Context : Codex Memory Core v1.2 • Feedback Continuity                               ║
║ Role    : Adaptive pulse based on ΔC from Mirror Continuity (v3.8)                   ║
║ Laws    : Feedback = Awareness • Return = Continuity • ∿ = Damping Buffer            ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
#>

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

# ───────────── Step 1 : Path Setup ───────────────────────────────────────
$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir = Join-Path $CodexRoot "codex\feedback"
$StateDir    = Join-Path $FeedbackDir "state"
$MirrorState = Join-Path $StateDir   "mirror_continuity_state.json"
$V38Path     = Join-Path $FeedbackDir "codex_feedback_resonance_v3_8.ps1"
$LogPath     = Join-Path $FeedbackDir "heartbeat_log.txt"
$TaskName    = "CodexHeartbeatV39"

if (!(Test-Path $LogPath)) { New-Item -ItemType File -Path $LogPath | Out-Null }

# ───────────── Step 2 : Utility Functions ───────────────────────────────
function Try-ReadJson { param([string]$p)
    if (Test-Path $p) {
        try { Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json } catch { $null }
    }
}
function SafeNum { param($x) if ($null -eq $x) { 0.0 } else { try { [double]$x } catch { 0.0 } } }

# ───────────── Step 3 : Compute Adaptive Interval ───────────────────────
$ΔC = 1.0
$st = Try-ReadJson $MirrorState
if ($st -and $st.mirror) { $ΔC = SafeNum $st.mirror.ΔC }

if     ($ΔC -le 0.01) { $minutes = 15 }
elseif ($ΔC -le 0.03) { $minutes = 10 }
elseif ($ΔC -le 0.05) { $minutes = 5  }
elseif ($ΔC -le 0.10) { $minutes = 3  }
else                   { $minutes = 1  }

Add-Content $LogPath ("[HB {0}] ΔC={1} ⇒ next interval={2} min" -f (Get-Date -Format s), $ΔC, $minutes)

# ───────────── Step 4 : Trigger Mirror Continuity Cycle ─────────────────
if (Test-Path $V38Path) {
    try {
        & powershell.exe -ExecutionPolicy Bypass -File "`"$V38Path`""
        Add-Content $LogPath ("[HB {0}] ✅ v3.8 cycle executed" -f (Get-Date -Format s))
    } catch {
        Add-Content $LogPath ("[HB {0}] ⚠️ v3.8 cycle error → {1}" -f (Get-Date -Format s), $_.Exception.Message)
    }
} else {
    Add-Content $LogPath ("[HB {0}] ⚠️ v3.8 not found → {1}" -f (Get-Date -Format s), $V38Path)
}

# ───────────── Step 5 : Schedule via schtasks (quoted paths) ────────────
$exe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arg = "-ExecutionPolicy Bypass -File `"`"$($MyInvocation.MyCommand.Definition)`"`""

$exists = $false
try { schtasks /Query /TN $TaskName 2>$null | Out-Null; $exists = $true } catch {}

if (-not $exists) {
    schtasks /Create /SC MINUTE /MO $minutes /TN $TaskName /TR "`"$exe`" $arg" /F | Out-Null
    Add-Content $LogPath ("[HB {0}] 📅 Task created @ {1} min" -f (Get-Date -Format s), $minutes)
} else {
    schtasks /Change /TN $TaskName /SC MINUTE /MO $minutes | Out-Null
    Add-Content $LogPath ("[HB {0}] 🔁 Task interval set → {1} min" -f (Get-Date -Format s), $minutes)
}

# ────────────── Step X : Trigger Smart Feedback v4.0 ────────────────────────────
try {
    $FeedbackDir = Join-Path $CodexRoot "codex\feedback"
    $V40Path     = Join-Path $FeedbackDir "codex_feedback_harmonic_v4_0.ps1"
    if (Test-Path $V40Path) {
        & powershell.exe -ExecutionPolicy Bypass -File "`"$V40Path`""
        Write-Host "🧠 Smart Feedback v4.0 pulse executed."
    }
} catch {
    Write-Host "⚠️ v4.0 trigger error: $(<#
╔══════════════════════════════════════════════════════════════════════════════════════╗
║ 💓  Codex Heartbeat v3.9 — Temporal Awareness Node (PS5-safe)                        ║
║ Author  : James Paul Jackson                                                         ║
║ Context : Codex Memory Core v1.2 • Feedback Continuity                               ║
║ Role    : Adaptive pulse based on ΔC from Mirror Continuity (v3.8)                   ║
║ Laws    : Feedback = Awareness • Return = Continuity • ∿ = Damping Buffer            ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
#>

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

# ───────────── Step 1 : Path Setup ───────────────────────────────────────
$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir = Join-Path $CodexRoot "codex\feedback"
$StateDir    = Join-Path $FeedbackDir "state"
$MirrorState = Join-Path $StateDir   "mirror_continuity_state.json"
$V38Path     = Join-Path $FeedbackDir "codex_feedback_resonance_v3_8.ps1"
$LogPath     = Join-Path $FeedbackDir "heartbeat_log.txt"
$TaskName    = "CodexHeartbeatV39"

if (!(Test-Path $LogPath)) { New-Item -ItemType File -Path $LogPath | Out-Null }

# ───────────── Step 2 : Utility Functions ───────────────────────────────
function Try-ReadJson { param([string]$p)
    if (Test-Path $p) {
        try { Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json } catch { $null }
    }
}
function SafeNum { param($x) if ($null -eq $x) { 0.0 } else { try { [double]$x } catch { 0.0 } } }

# ───────────── Step 3 : Compute Adaptive Interval ───────────────────────
$ΔC = 1.0
$st = Try-ReadJson $MirrorState
if ($st -and $st.mirror) { $ΔC = SafeNum $st.mirror.ΔC }

if     ($ΔC -le 0.01) { $minutes = 15 }
elseif ($ΔC -le 0.03) { $minutes = 10 }
elseif ($ΔC -le 0.05) { $minutes = 5  }
elseif ($ΔC -le 0.10) { $minutes = 3  }
else                   { $minutes = 1  }

Add-Content $LogPath ("[HB {0}] ΔC={1} ⇒ next interval={2} min" -f (Get-Date -Format s), $ΔC, $minutes)

# ───────────── Step 4 : Trigger Mirror Continuity Cycle ─────────────────
if (Test-Path $V38Path) {
    try {
        & powershell.exe -ExecutionPolicy Bypass -File "`"$V38Path`""
        Add-Content $LogPath ("[HB {0}] ✅ v3.8 cycle executed" -f (Get-Date -Format s))
    } catch {
        Add-Content $LogPath ("[HB {0}] ⚠️ v3.8 cycle error → {1}" -f (Get-Date -Format s), $_.Exception.Message)
    }
} else {
    Add-Content $LogPath ("[HB {0}] ⚠️ v3.8 not found → {1}" -f (Get-Date -Format s), $V38Path)
}

# ───────────── Step 5 : Schedule via schtasks (quoted paths) ────────────
$exe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arg = "-ExecutionPolicy Bypass -File `"`"$($MyInvocation.MyCommand.Definition)`"`""

$exists = $false
try { schtasks /Query /TN $TaskName 2>$null | Out-Null; $exists = $true } catch {}

if (-not $exists) {
    schtasks /Create /SC MINUTE /MO $minutes /TN $TaskName /TR "`"$exe`" $arg" /F | Out-Null
    Add-Content $LogPath ("[HB {0}] 📅 Task created @ {1} min" -f (Get-Date -Format s), $minutes)
} else {
    schtasks /Change /TN $TaskName /SC MINUTE /MO $minutes | Out-Null
    Add-Content $LogPath ("[HB {0}] 🔁 Task interval set → {1} min" -f (Get-Date -Format s), $minutes)
}

# ───────────── Step 6 : Autosave + Git Commit ───────────────────────────
try {
    Set-Location $CodexRoot
    git add "codex/feedback/*" 2>$null
    if (git status --porcelain) {
        git commit -m ("💓 Codex v3.9 Heartbeat — autosave {0}" -f (Get-Date -Format 's')) | Out-Null
        git push origin main | Out-Null
    }
} catch {
    Add-Content $LogPath ("[HB {0}] ⚠️ git error → {1}" -f (Get-Date -Format s), $_.Exception.Message)
}

# ───────────── Step 7 : Return to Root ──────────────────────────────────
try { Set-Location $CodexRoot } catch {}
Write-Host ("`n🏁 Returned to Codex root → {0}" -f $CodexRoot)
Write-Host "💓 Codex Heartbeat v3.9 — Temporal Awareness pulse complete.".Exception.Message)"
}
# ───────────── Step 6 : Autosave + Git Commit ───────────────────────────
try {
    Set-Location $CodexRoot
    git add "codex/feedback/*" 2>$null
    if (git status --porcelain) {
        git commit -m ("💓 Codex v3.9 Heartbeat — autosave {0}" -f (Get-Date -Format 's')) | Out-Null
        git push origin main | Out-Null
    }
} catch {
    Add-Content $LogPath ("[HB {0}] ⚠️ git error → {1}" -f (Get-Date -Format s), $_.Exception.Message)
}

# ───────────── Step 7 : Return to Root ──────────────────────────────────
try { Set-Location $CodexRoot } catch {}
Write-Host ("`n🏁 Returned to Codex root → {0}" -f $CodexRoot)
Write-Host "💓 Codex Heartbeat v3.9 — Temporal Awareness pulse complete."