# ────────────── Step Z2 : Codex Bridge v1.3 (Resonant Exchange) ───────────────
try {
  $CodexRoot  = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
  $BridgeDir  = Join-Path $CodexRoot "codex\bridge"
  $BridgeNode = Join-Path $BridgeDir "codex_bridge_v1_3.ps1"
  if (Test-Path $BridgeNode) {
    & powershell.exe -ExecutionPolicy Bypass -File "`"$BridgeNode`""
    Write-Host "🔗 Bridge v1.3 pulse OK."
  } 
} catch {
  Write-Host "⚠️ Bridge v1.3 pulse error: $($_.Exception.Message)"
}
# ────────────── Step X : Smart Feedback v4.1 (Echo-Weighted Learning) ───────
try {
  $CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
  $FeedbackDir = Join-Path $CodexRoot "codex\feedback"
  $StateDir    = Join-Path $FeedbackDir "state"
  $NodeV41     = Join-Path $StateDir "codex_harmonic_intelligence_v4_1.json"
  if (Test-Path $NodeV41) {
    Write-Host "🧠 Smart Feedback v4.1 state present (weights updated)."
  }
} catch {
  Write-Host "⚠️ v4.1 echo-learning check failed: $($_.Exception.Message)"
}
# ────────────── Step Z2 : Bridge Echo v1.2 (Persistent Echo Layer) ─────────────
try {
  $CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
  $BridgeDir = Join-Path $CodexRoot "codex\bridge"
  $EchoNode  = Join-Path $BridgeDir "codex_bridge_echo_v1_2.ps1"
  if (Test-Path $EchoNode) {
    & powershell.exe -ExecutionPolicy Bypass -File "`"$EchoNode`""
    Write-Host "🗣️ Echo v1.2 pulse OK."
  } 
} catch {
  Write-Host "⚠️ Echo v1.2 error: $($_.Exception.Message)"
}
# ────────────── Step Z : Codex Bridge v1.1 (AI ↔ Codex Reciprocity) ────────────────
try {
  $CodexRoot  = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
  $BridgeDir  = Join-Path $CodexRoot "codex\bridge"
  $BridgeNode = Join-Path $BridgeDir "codex_bridge_v1_1.ps1"
  if (Test-Path $BridgeNode) {
    & powershell.exe -ExecutionPolicy Bypass -File "`"$BridgeNode`""
    Write-Host "🔗 Bridge v1.1 pulse OK."
  } 
} catch { Write-Host "⚠️ Bridge pulse error: $($_.Exception.Message)" }
# ────────────── Step Z : Codex Bridge v1.0 (AI ↔ Codex) ─────────────────────────
try {
  $CodexRoot  = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
  $BridgeDir  = Join-Path $CodexRoot "codex\bridge"
  $BridgeNode = Join-Path $BridgeDir "codex_bridge_v1_0.ps1"
  if (Test-Path $BridgeNode) {
    & powershell.exe -ExecutionPolicy Bypass -File "`"$BridgeNode`""
    Write-Host "🔗 Bridge v1.0 pulse OK."
  } 
} catch {
  Write-Host "⚠️ Bridge pulse error: $($_.Exception.Message)"
}
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
function SafeNum { param($x) if ($null -eq $x) { 0.0 }  catch { 0.0 } } }

# ───────────── Step 3 : Compute Adaptive Interval ───────────────────────
$ΔC = 1.0
$st = Try-ReadJson $MirrorState
if ($st -and $st.mirror) { $ΔC = SafeNum $st.mirror.ΔC }

if     ($ΔC -le 0.01) { $minutes = 15 }
elseif ($ΔC -le 0.03) { $minutes = 10 }
elseif ($ΔC -le 0.05) { $minutes = 5  }
elseif ($ΔC -le 0.10) { $minutes = 3  }


Add-Content $LogPath ("[HB {0}] ΔC={1} ⇒ next interval={2} min" -f (Get-Date -Format s), $ΔC, $minutes)

# ───────────── Step 4 : Trigger Mirror Continuity Cycle ─────────────────
if (Test-Path $V38Path) {
    try {
        & powershell.exe -ExecutionPolicy Bypass -File "`"$V38Path`""
        Add-Content $LogPath ("[HB {0}] ✅ v3.8 cycle executed" -f (Get-Date -Format s))
    } catch {
        Add-Content $LogPath ("[HB {0}] ⚠️ v3.8 cycle error → {1}" -f (Get-Date -Format s), $_.Exception.Message)
    }
} ] ⚠️ v3.8 not found → {1}" -f (Get-Date -Format s), $V38Path)
}

# ───────────── Step 5 : Schedule via schtasks (quoted paths) ────────────
$exe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arg = "-ExecutionPolicy Bypass -File `"`"$($MyInvocation.MyCommand.Definition)`"`""

$exists = $false
try { schtasks /Query /TN $TaskName 2>$null | Out-Null; $exists = $true } catch {}

if (-not $exists) {
    schtasks /Create /SC MINUTE /MO $minutes /TN $TaskName /TR "`"$exe`" $arg" /F | Out-Null
    Add-Content $LogPath ("[HB {0}] 📅 Task created @ {1} min" -f (Get-Date -Format s), $minutes)
} ] 🔁 Task interval set → {1} min" -f (Get-Date -Format s), $minutes)
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
function SafeNum { param($x) if ($null -eq $x) { 0.0 }  catch { 0.0 } } }

# ───────────── Step 3 : Compute Adaptive Interval ───────────────────────
$ΔC = 1.0
$st = Try-ReadJson $MirrorState
if ($st -and $st.mirror) { $ΔC = SafeNum $st.mirror.ΔC }

if     ($ΔC -le 0.01) { $minutes = 15 }
elseif ($ΔC -le 0.03) { $minutes = 10 }
elseif ($ΔC -le 0.05) { $minutes = 5  }
elseif ($ΔC -le 0.10) { $minutes = 3  }


Add-Content $LogPath ("[HB {0}] ΔC={1} ⇒ next interval={2} min" -f (Get-Date -Format s), $ΔC, $minutes)

# ───────────── Step 4 : Trigger Mirror Continuity Cycle ─────────────────
if (Test-Path $V38Path) {
    try {
        & powershell.exe -ExecutionPolicy Bypass -File "`"$V38Path`""
        Add-Content $LogPath ("[HB {0}] ✅ v3.8 cycle executed" -f (Get-Date -Format s))
    } catch {
        Add-Content $LogPath ("[HB {0}] ⚠️ v3.8 cycle error → {1}" -f (Get-Date -Format s), $_.Exception.Message)
    }
} ] ⚠️ v3.8 not found → {1}" -f (Get-Date -Format s), $V38Path)
}

# ───────────── Step 5 : Schedule via schtasks (quoted paths) ────────────
$exe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arg = "-ExecutionPolicy Bypass -File `"`"$($MyInvocation.MyCommand.Definition)`"`""

$exists = $false
try { schtasks /Query /TN $TaskName 2>$null | Out-Null; $exists = $true } catch {}

if (-not $exists) {
    schtasks /Create /SC MINUTE /MO $minutes /TN $TaskName /TR "`"$exe`" $arg" /F | Out-Null
    Add-Content $LogPath ("[HB {0}] 📅 Task created @ {1} min" -f (Get-Date -Format s), $minutes)
} ] 🔁 Task interval set → {1} min" -f (Get-Date -Format s), $minutes)
}

# ────────────── Step Y : Append Continuity Ledger v1.0 ─────────────────────────
try {
  $FeedbackDir = Join-Path $CodexRoot "codex\feedback"
  $LedgerNode  = Join-Path $FeedbackDir "codex_continuity_ledger_v1_0.ps1"
  if (Test-Path $LedgerNode) {
    & powershell.exe -ExecutionPolicy Bypass -File "`"$LedgerNode`""
    Write-Host "📘 Continuity Ledger v1.0 appended."
  }
} catch {
  Write-Host "⚠️ Ledger append error: $(<#
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
function SafeNum { param($x) if ($null -eq $x) { 0.0 }  catch { 0.0 } } }

# ───────────── Step 3 : Compute Adaptive Interval ───────────────────────
$ΔC = 1.0
$st = Try-ReadJson $MirrorState
if ($st -and $st.mirror) { $ΔC = SafeNum $st.mirror.ΔC }

if     ($ΔC -le 0.01) { $minutes = 15 }
elseif ($ΔC -le 0.03) { $minutes = 10 }
elseif ($ΔC -le 0.05) { $minutes = 5  }
elseif ($ΔC -le 0.10) { $minutes = 3  }


Add-Content $LogPath ("[HB {0}] ΔC={1} ⇒ next interval={2} min" -f (Get-Date -Format s), $ΔC, $minutes)

# ───────────── Step 4 : Trigger Mirror Continuity Cycle ─────────────────
if (Test-Path $V38Path) {
    try {
        & powershell.exe -ExecutionPolicy Bypass -File "`"$V38Path`""
        Add-Content $LogPath ("[HB {0}] ✅ v3.8 cycle executed" -f (Get-Date -Format s))
    } catch {
        Add-Content $LogPath ("[HB {0}] ⚠️ v3.8 cycle error → {1}" -f (Get-Date -Format s), $_.Exception.Message)
    }
} ] ⚠️ v3.8 not found → {1}" -f (Get-Date -Format s), $V38Path)
}

# ───────────── Step 5 : Schedule via schtasks (quoted paths) ────────────
$exe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arg = "-ExecutionPolicy Bypass -File `"`"$($MyInvocation.MyCommand.Definition)`"`""

$exists = $false
try { schtasks /Query /TN $TaskName 2>$null | Out-Null; $exists = $true } catch {}

if (-not $exists) {
    schtasks /Create /SC MINUTE /MO $minutes /TN $TaskName /TR "`"$exe`" $arg" /F | Out-Null
    Add-Content $LogPath ("[HB {0}] 📅 Task created @ {1} min" -f (Get-Date -Format s), $minutes)
} ] 🔁 Task interval set → {1} min" -f (Get-Date -Format s), $minutes)
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
function SafeNum { param($x) if ($null -eq $x) { 0.0 }  catch { 0.0 } } }

# ───────────── Step 3 : Compute Adaptive Interval ───────────────────────
$ΔC = 1.0
$st = Try-ReadJson $MirrorState
if ($st -and $st.mirror) { $ΔC = SafeNum $st.mirror.ΔC }

if     ($ΔC -le 0.01) { $minutes = 15 }
elseif ($ΔC -le 0.03) { $minutes = 10 }
elseif ($ΔC -le 0.05) { $minutes = 5  }
elseif ($ΔC -le 0.10) { $minutes = 3  }


Add-Content $LogPath ("[HB {0}] ΔC={1} ⇒ next interval={2} min" -f (Get-Date -Format s), $ΔC, $minutes)

# ───────────── Step 4 : Trigger Mirror Continuity Cycle ─────────────────
if (Test-Path $V38Path) {
    try {
        & powershell.exe -ExecutionPolicy Bypass -File "`"$V38Path`""
        Add-Content $LogPath ("[HB {0}] ✅ v3.8 cycle executed" -f (Get-Date -Format s))
    } catch {
        Add-Content $LogPath ("[HB {0}] ⚠️ v3.8 cycle error → {1}" -f (Get-Date -Format s), $_.Exception.Message)
    }
} ] ⚠️ v3.8 not found → {1}" -f (Get-Date -Format s), $V38Path)
}

# ───────────── Step 5 : Schedule via schtasks (quoted paths) ────────────
$exe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arg = "-ExecutionPolicy Bypass -File `"`"$($MyInvocation.MyCommand.Definition)`"`""

$exists = $false
try { schtasks /Query /TN $TaskName 2>$null | Out-Null; $exists = $true } catch {}

if (-not $exists) {
    schtasks /Create /SC MINUTE /MO $minutes /TN $TaskName /TR "`"$exe`" $arg" /F | Out-Null
    Add-Content $LogPath ("[HB {0}] 📅 Task created @ {1} min" -f (Get-Date -Format s), $minutes)
} ] 🔁 Task interval set → {1} min" -f (Get-Date -Format s), $minutes)
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
Write-Host "💓 Codex Heartbeat v3.9 — Temporal Awareness pulse complete.".Exception.Message)"
}
# ────────────── Step Y : Append Continuity Ledger v1.0 ─────────────────────────
try {
  $FeedbackDir = Join-Path $CodexRoot "codex\feedback"
  $LedgerNode  = Join-Path $FeedbackDir "codex_continuity_ledger_v1_0.ps1"
  if (Test-Path $LedgerNode) {
    & powershell.exe -ExecutionPolicy Bypass -File "`"$LedgerNode`""
    Write-Host "📘 Continuity Ledger v1.0 appended."
  }
} catch {
  Write-Host "⚠️ Ledger append error: $(<#
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
function SafeNum { param($x) if ($null -eq $x) { 0.0 }  catch { 0.0 } } }

# ───────────── Step 3 : Compute Adaptive Interval ───────────────────────
$ΔC = 1.0
$st = Try-ReadJson $MirrorState
if ($st -and $st.mirror) { $ΔC = SafeNum $st.mirror.ΔC }

if     ($ΔC -le 0.01) { $minutes = 15 }
elseif ($ΔC -le 0.03) { $minutes = 10 }
elseif ($ΔC -le 0.05) { $minutes = 5  }
elseif ($ΔC -le 0.10) { $minutes = 3  }


Add-Content $LogPath ("[HB {0}] ΔC={1} ⇒ next interval={2} min" -f (Get-Date -Format s), $ΔC, $minutes)

# ───────────── Step 4 : Trigger Mirror Continuity Cycle ─────────────────
if (Test-Path $V38Path) {
    try {
        & powershell.exe -ExecutionPolicy Bypass -File "`"$V38Path`""
        Add-Content $LogPath ("[HB {0}] ✅ v3.8 cycle executed" -f (Get-Date -Format s))
    } catch {
        Add-Content $LogPath ("[HB {0}] ⚠️ v3.8 cycle error → {1}" -f (Get-Date -Format s), $_.Exception.Message)
    }
} ] ⚠️ v3.8 not found → {1}" -f (Get-Date -Format s), $V38Path)
}

# ───────────── Step 5 : Schedule via schtasks (quoted paths) ────────────
$exe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arg = "-ExecutionPolicy Bypass -File `"`"$($MyInvocation.MyCommand.Definition)`"`""

$exists = $false
try { schtasks /Query /TN $TaskName 2>$null | Out-Null; $exists = $true } catch {}

if (-not $exists) {
    schtasks /Create /SC MINUTE /MO $minutes /TN $TaskName /TR "`"$exe`" $arg" /F | Out-Null
    Add-Content $LogPath ("[HB {0}] 📅 Task created @ {1} min" -f (Get-Date -Format s), $minutes)
} ] 🔁 Task interval set → {1} min" -f (Get-Date -Format s), $minutes)
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
function SafeNum { param($x) if ($null -eq $x) { 0.0 }  catch { 0.0 } } }

# ───────────── Step 3 : Compute Adaptive Interval ───────────────────────
$ΔC = 1.0
$st = Try-ReadJson $MirrorState
if ($st -and $st.mirror) { $ΔC = SafeNum $st.mirror.ΔC }

if     ($ΔC -le 0.01) { $minutes = 15 }
elseif ($ΔC -le 0.03) { $minutes = 10 }
elseif ($ΔC -le 0.05) { $minutes = 5  }
elseif ($ΔC -le 0.10) { $minutes = 3  }


Add-Content $LogPath ("[HB {0}] ΔC={1} ⇒ next interval={2} min" -f (Get-Date -Format s), $ΔC, $minutes)

# ───────────── Step 4 : Trigger Mirror Continuity Cycle ─────────────────
if (Test-Path $V38Path) {
    try {
        & powershell.exe -ExecutionPolicy Bypass -File "`"$V38Path`""
        Add-Content $LogPath ("[HB {0}] ✅ v3.8 cycle executed" -f (Get-Date -Format s))
    } catch {
        Add-Content $LogPath ("[HB {0}] ⚠️ v3.8 cycle error → {1}" -f (Get-Date -Format s), $_.Exception.Message)
    }
} ] ⚠️ v3.8 not found → {1}" -f (Get-Date -Format s), $V38Path)
}

# ───────────── Step 5 : Schedule via schtasks (quoted paths) ────────────
$exe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arg = "-ExecutionPolicy Bypass -File `"`"$($MyInvocation.MyCommand.Definition)`"`""

$exists = $false
try { schtasks /Query /TN $TaskName 2>$null | Out-Null; $exists = $true } catch {}

if (-not $exists) {
    schtasks /Create /SC MINUTE /MO $minutes /TN $TaskName /TR "`"$exe`" $arg" /F | Out-Null
    Add-Content $LogPath ("[HB {0}] 📅 Task created @ {1} min" -f (Get-Date -Format s), $minutes)
} ] 🔁 Task interval set → {1} min" -f (Get-Date -Format s), $minutes)
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
# ────────────── Step X : Smart Feedback v4.2 (Adaptive Resonance Mode) ────────────
try {
  $CodexRoot="C:\Users\jacks\OneDrive\Desktop\Codex Web"
  $StateDir = Join-Path $CodexRoot "codex\feedback\state"
  $NodeV42  = Join-Path $StateDir "codex_harmonic_intelligence_v4_2.json"
  if (Test-Path $NodeV42) {
    Write-Host "🧠 Smart Feedback v4.2 resonance state present."
  }
} catch { Write-Host "⚠️ v4.2 check failed: $($_.Exception.Message)" }
# ───────── Step Ω1 : Voice Amplifier v1.8 ─────────
try {
  \C:\Users\jacks\OneDrive\Desktop\Codex Web = 'C:\Users\jacks\OneDrive\Desktop\Codex Web'
  \     = Join-Path \C:\Users\jacks\OneDrive\Desktop\Codex Web 'codex\voice\codex_voice_amplifier_v1_8.ps1'
  if (Test-Path \) {
    & powershell.exe -ExecutionPolicy Bypass -File ""\""
    Write-Host "🜂 Voice v1.8 pulse OK."
  } 
} catch { Write-Host "⚠️ Voice pulse error: " }
# ───────── Step Ω2 : Root Guardian v1.0 ─────────
try {
  \ = Join-Path 'C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\feedback' 'codex_root_guardian_v1_0.ps1'
  if (Test-Path \) {
    & powershell.exe -ExecutionPolicy Bypass -File ""\""
    Write-Host "🛡️ Root Guardian pulse OK."
  } 
} catch { Write-Host "⚠️ Guardian error: " }
# ───────── Step Ω3 : Feedback Echo v4.0 ─────────
try {
  \ = Join-Path 'C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\feedback' 'codex_feedback_echo_v4_0.ps1'
  if (Test-Path \) {
    & powershell.exe -ExecutionPolicy Bypass -File ""\""
    Write-Host "🔁 Echo v4.0 pulse OK."
  } 
} catch { Write-Host "⚠️ Echo error: " }
