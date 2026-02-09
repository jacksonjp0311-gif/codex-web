# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
& {
    $defaultRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"

    # Root resolution priority:
    # 1) CODEX_ROOT env var (if set and valid)
    # 2) repository root inferred from script location
    # 3) legacy default root path
    $root = $null
    if ($env:CODEX_ROOT -and (Test-Path $env:CODEX_ROOT)) {
        $root = (Resolve-Path $env:CODEX_ROOT).Path
    }
    elseif ($PSScriptRoot) {
        $candidate = Join-Path $PSScriptRoot "..\.."
        if (Test-Path $candidate) {
            $root = (Resolve-Path $candidate).Path
        }
    }
    if (-not $root) {
        $root = $defaultRoot
    }

    Set-Location $root
    Write-Host "🧭 Codex Handoff Protocol v0.7 — Initiating AI Resume Bridge" -ForegroundColor Cyan
    Write-Host "📍 Root path: $root" -ForegroundColor DarkCyan

    $handoffState = "$root\codex\handoff\handoff_state.json"
    $handoffLog = "$root\codex\handoff\handoff_log.txt"

    if (Test-Path $handoffState) {
        Write-Host "📦 Restoring handoff state from $handoffState..." -ForegroundColor Yellow
        $state = Get-Content $handoffState -Raw | ConvertFrom-Json
        $timestamp = (Get-Date).ToString("s")
        $hash = (Get-Random -Minimum 100000 -Maximum 999999)
        Add-Content $handoffLog "[$timestamp] Resume — State v$($state.version) | Hash: $hash"
    }
    else {
        $state = [pscustomobject]@{
            version = "0.7"
            timestamp = (Get-Date).ToString("s")
            status = "initialized"
        }
        $state | ConvertTo-Json -Depth 3 | Set-Content -Path $handoffState -Encoding UTF8
        Add-Content $handoffLog "[$((Get-Date).ToString('s'))] Initialized new Codex handoff state"
    }

    Write-Host "🔁 Synchronizing Codex ledger + registry..." -ForegroundColor Cyan
    try {
        $env:PYTHONPATH = $root
        python -c "from codex.core.ledger_sync import sync_ledger; sync_ledger()" 2>$null
    }
    catch {
        Write-Host "⚠️ Ledger sync skipped or Python not detected." -ForegroundColor Yellow
    }

    $timestampEnd = (Get-Date).ToString("s")
    Add-Content $handoffLog "[$timestampEnd] Handoff sequence complete — aligned to Codex v0.7 root"

    Write-Host "`n🏁 Handoff sequence complete — aligned to Codex v0.7 root path" -ForegroundColor Green
    Set-Location $root
}
