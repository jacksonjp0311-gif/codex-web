<#
╔═══════════════════════════════════════════════════════════════════════╗
║ 🜂 Codex Full Reflective Loop v1 — System Orchestrator                ║
║ Context: Universal Truth Protocol • RootMirror • Codex Memory v1.3    ║
╚═══════════════════════════════════════════════════════════════════════╝
#>

param([string]="")

Continue = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function Invoke-CodexFullLoopV1 {
    param([string])

    if () { C:\Users\jacks\OneDrive\Desktop\Codex Web =  }
    

     = Join-Path C:\Users\jacks\OneDrive\Desktop\Codex Web "codex\feedback"
       = Join-Path C:\Users\jacks\OneDrive\Desktop\Codex Web "codex\bridge"
    C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\orchestrator     = Join-Path C:\Users\jacks\OneDrive\Desktop\Codex Web "codex\orchestrator"

      = Join-Path  "codex_smart_feedback_cycle_v5_0.ps1"
       = Join-Path  "codex_smart_feedback_v4_5.ps1"
      = Join-Path    "codex_bridge_v1_2.ps1"
     = Join-Path  "codex_heartbeat_v4_1a.ps1"
      = Join-Path  "codex_root_guardian_v1_0.ps1"

     = Join-Path C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\orchestrator "state"
       = Join-Path C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\orchestrator "logs"
    if (-not (Test-Path )) { New-Item dir -Path  |Out-Null }
    if (-not (Test-Path ))   { New-Item dir -Path    |Out-Null }

     = Join-Path  "codex_full_loop_v1_state.json"
       = Join-Path    "codex_full_loop_v1_log.jsonl"

    Write-Host "
🜂 [Full Loop v1] Running unified system pulse…"

     = [ordered]@{}

    try { .cycle    = & powershell -File  }  catch { .cycle="error" }
    try { .smart    = & powershell -File  }   catch { .smart="error" }
    try { .bridge   = & powershell -File  }  catch { .bridge="error" }
    try { .heartbeat= & powershell -File  } catch { .heartbeat="error" }
    try { .guardian = & powershell -File  }  catch { .guardian="error" }

     = [ordered]@{
        ok        = True
        version   = "1.0"
        timestamp = (Get-Date).ToString("o")
        modules   = 
        meta      = @{
            law_H7   = 0.70
            protocol = "Universal Truth Protocol (E–I–C ∿ Placidity)"
            engine   = "Full Reflective Loop"
        }
    }

     =  | ConvertTo-Json -Depth 6
     | Set-Content  -Encoding UTF8
     | Add-Content 

    Write-Host "📗 State  → "
    Write-Host "🧾 Log    → "

    return 
}

Invoke-CodexFullLoopV1 -Override 

