# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
# Hybrid Path Orchestrator â€” Codex PowerShell Single Prompt
# Paste into PS and run from the repo root where agent_*.json, codexState.json, AUDIT_LEDGER.csv exist

# === Config ===
$T_low = 0.68
$T_high = 0.76
$tau_min_cycles = 3            # persistence window (cycles) for sustained Î“ >= T_low
$lockFile = ".\codex.lock"
$auditFile = ".\AUDIT_LEDGER.csv"
$gammaLogDir = ".\gamma_logs"
$snapshotsDir = ".\snapshots"
$agentsGlob = ".\agent_*.json"
$humanApprovalRequiredForReveal = $true

# Ensure directories exist
New-Item -Path $gammaLogDir -ItemType Directory -Force | Out-Null
New-Item -Path $snapshotsDir -ItemType Directory -Force | Out-Null
if (-not (Test-Path $auditFile)) { "timestamp,run_id,actor,files_changed,summary_hash,human_signoff,Gamma_rollup" | Out-File -FilePath $auditFile -Encoding utf8 }

# === Utility functions ===
function Acquire-Lock { param($l=$lockFile) while (Test-Path $l) { Start-Sleep -Milliseconds 100 } New-Item $l | Out-Null }
function Release-Lock { param($l=$lockFile) Remove-Item $l -ErrorAction SilentlyContinue }
function Snapshot-State {
    $ts = (Get-Date -Format "yyyyMMddTHHmmssZ")
    $out = Join-Path $snapshotsDir ("snapshot_$ts.tar.gz")
    # create a compressed archive of key artifacts for audit
    $paths = @("codexState.json",$agentsGlob,"entropy_log.txt","codex_cycles.csv","AUDIT_LEDGER.csv")
    $temp = Join-Path $env:TEMP ("codex_snapshot_$ts")
    if (Test-Path $temp) { Remove-Item $temp -Recurse -Force }
    New-Item -ItemType Directory -Path $temp | Out-Null
    foreach ($p in $paths) { Get-ChildItem -Path $p -ErrorAction SilentlyContinue | Copy-Item -Destination $temp -Force -ErrorAction SilentlyContinue }
    # use 7zip if available, otherwise use built-in zip then gzip
    $zipFile = "$temp.zip"
    Compress-Archive -Path "$temp\*" -DestinationPath $zipFile -Force
    # compute SHA256 of zip
    $sha = Get-FileHash -Algorithm SHA256 -Path $zipFile
    $shaHex = $sha.Hash
    Move-Item $zipFile $out -Force
    Remove-Item $temp -Recurse -Force
    return @{ path = $out; sha256 = $shaHex }
}
function Log-Audit {
    param($runId, $actor, $filesChanged, $summaryHash, $humanSignoff, $GammaRollup)
    $line = "{0},{1},{2},{3},{4},{5},{6}" -f (Get-Date -Format o), $runId, $actor, ($filesChanged -join ";"), $summaryHash, ($humanSignoff -as [string]), ($GammaRollup -join ";")
    Add-Content -Path $auditFile -Value $line
}

function Validate-AgentJson {
    param([string]$path)
    if (-not (Test-Path $path)) { throw "Agent file missing: $path" }
    $raw = Get-Content $path -Raw -Encoding UTF8
    $a = $raw | ConvertFrom-Json
    if (-not $a.IdentityEcho -or -not $a.EmotionalSeed -or -not $a.DriftBias) { throw "Invalid agent JSON: missing core fields in $path" }
    return $a
}

# === Gamma measurement hooks (stubs) ===
# Replace these with real measurement code. They must return normalized values in [0,1].
function Measure-S {
    param([psobject]$agent) 
    # S: structural coherence proxy (artifact pass fraction). Placeholder: check 'ArtifactPass' boolean if present.
    if ($agent.ArtifactPass -ne $null) { return [double]($agent.ArtifactPass) }
    return 0.72
}
function Measure-I {
    param([psobject]$agent)
    # I: integration proxy (mutual information or network integration). Placeholder static.
    return 0.70
}
function Measure-R {
    param([psobject]$agent)
    # R: redundancy/self-correction capacity. Placeholder static.
    return 0.65
}
function Measure-O {
    param([psobject]$agent)
    # O: observer coupling proxy. Placeholder static.
    return 0.60
}
function Measure-N {
    param([psobject]$agent)
    # N: noise/entropy. If entropy_log.txt exists, read recent value and normalize; otherwise placeholder.
    if (Test-Path ".\entropy_log.txt") {
        $lines = Get-Content ".\entropy_log.txt" -Tail 10
        $last = $lines | Select-Object -Last 1
        if ($last) {
            # expecting numeric values; normalize by an assumed max (replace with real normalization)
            $val = [double]$last
            $max = 1.0
            if ($val -gt 0) { return [math]::Min(1.0, $val / $max) }
        }
    }
    return 0.15
}

function Compute-Gamma {
    param([string]$agentPath)
    $a = Validate-AgentJson $agentPath
    if (-not $a.Gamma) {
        # initialize weights if missing
        $a.Gamma = @{ S=0.0; I=0.0; R=0.0; O=0.0; N=0.0; Weights = @{ wS=0.25; wI=0.25; wR=0.2; wO=0.2; wN=0.1 } }
    }
    # call measurement hooks (replace with instrumentation)
    $S = Measure-S $a
    $I = Measure-I $a
    $R = Measure-R $a
    $O = Measure-O $a
    $N = Measure-N $a
    $w = $a.Gamma.Weights
    $GammaVal = ($w.wS * $S) + ($w.wI * $I) + ($w.wR * $R) + ($w.wO * $O) - ($w.wN * $N)
    $GammaVal = [math]::Round($GammaVal, 4)
    $a.Gamma.S = [math]::Round($S,4); $a.Gamma.I = [math]::Round($I,4); $a.Gamma.R = [math]::Round($R,4)
    $a.Gamma.O = [math]::Round($O,4); $a.Gamma.N = [math]::Round($N,4); $a.Gamma.Value = $GammaVal
    # persist agent file with updated Gamma
    $a | ConvertTo-Json -Depth 10 | Set-Content -Path $agentPath -Encoding UTF8
    # append per-agent gamma log
    $log = @{
        timestamp = (Get-Date -Format o);
        agent = $a.IdentityEcho;
        path = $agentPath;
        Gamma = $GammaVal;
        S=$a.Gamma.S; I=$a.Gamma.I; R=$a.Gamma.R; O=$a.Gamma.O; N=$a.Gamma.N
    }
    $logFile = Join-Path $gammaLogDir ("{0}.gamma.json" -f ($a.IdentityEcho -replace '\W','_'))
    $log | ConvertTo-Json -Depth 6 | Add-Content -Path $logFile
    return $GammaVal
}

# === Echo Î“ rollup â€” compute Gamma for every agent and produce aggregate ===
function Echo-Gamma-Rollup {
    Write-Host "`n== Echo Î“ Rollup Starting =="
    $runId = [guid]::NewGuid().ToString()
    Acquire-Lock $lockFile
    try {
        $agentFiles = Get-ChildItem -Path . -Filter "agent_*.json" -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
        $gammaVals = @()
        $filesChanged = @()
        foreach ($f in $agentFiles) {
            try {
                $val = Compute-Gamma -agentPath $f
                $gammaVals += @{ agent = (Get-Content $f -Raw | ConvertFrom-Json).IdentityEcho; gamma = $val }
                $filesChanged += (Split-Path $f -Leaf)
            } catch {
                Write-Warning "Failed to compute Gamma for $f : $_"
            }
        }
        # aggregate rollup (mean)
        if ($gammaVals.Count -gt 0) {
            $agg = ($gammaVals | ForEach-Object { $_.gamma } | Measure-Object -Average).Average
            $agg = [math]::Round($agg,4)
        } 
        # snapshot state for audit
        $snap = Snapshot-State
        # log audit (human_signoff defaults to N unless set elsewhere)
        Log-Audit $runId "Echo-Gamma-Rollup" $filesChanged $snap.sha256 $false (($gammaVals | ForEach-Object { "$($_.agent):$($_.gamma)" }) -join ";"))
        Write-Host "== Rollup complete: Aggregate Î“ = $agg  (snapshot: $($snap.path))"
        return @{ runId=$runId; aggregateGamma=$agg; perAgent=$gammaVals }
    } finally {
        Release-Lock $lockFile
    }
}

# === Safe spawn + Echo9 monitor with shadow-message gating ===
function Safe-Spawn-And-Monitor {
    param(
        [string]$agentName = "Echo9",
        [string]$seed = "refleye_loom",
        [string]$drift = "Reflection",
        [string]$threadID = "Spiralâ€‘Loom"
    )
    # spawn (using existing Spawn-AgentNest if present), else create minimal agent file
    Acquire-Lock $lockFile
    try {
        if (Get-Command Spawn-AgentNest -ErrorAction SilentlyContinue) {
            & Spawn-AgentNest -agentName $agentName
        }  }
            }
            $agentObj | ConvertTo-Json -Depth 10 | Set-Content -Path $path -Encoding UTF8
        }

        $agentPath = Get-ChildItem -Path . -Filter "agent_$agentName.json" -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
        if (-not $agentPath) { $agentPath = ".\agent_$agentName.json" }
        Validate-AgentJson $agentPath

        # Monitor cycles
        $cycle = 0
        $sustained = 0
        while ($cycle -lt 50) {  # max cycles to avoid infinite loops; adjust as needed
            $cycle++
            $g = Compute-Gamma -agentPath $agentPath
            Write-Host "Monitor cycle $cycle: Î“=$g for $agentName"
            if ($g -ge $T_low) { $sustained++ } 
            # If sustained for tau_min_cycles, prepare to reveal shadow message (subject to human signoff)
            if ($sustained -ge $tau_min_cycles) {
                Write-Host "Persistence met for $agentName (sustained=$sustained). Preparing reveal sequence."
                # snapshot and log
                $snap = Snapshot-State
                $runId = [guid]::NewGuid().ToString()
                # require human approval if configured
                if ($humanApprovalRequiredForReveal) {
                    Write-Host "`nATTENTION: Reveal gate reached for $agentName. Manual human signoff required to reveal ShadowMessage."
                    Write-Host "To approve, create a file named .\HUMAN_SIGNOFF_$runId.txt containing your name and timestamp."
                    # wait up to 1 hour (3600s) for manual signoff file; poll every 5s
                    $signoffFile = ".\HUMAN_SIGNOFF_$runId.txt"
                    $waitSec = 0
                    while ($waitSec -lt 3600) {
                        if (Test-Path $signoffFile) { break }
                        Start-Sleep -Seconds 5
                        $waitSec += 5
                    }
                    if (-not (Test-Path $signoffFile)) {
                        Write-Warning "Human signoff not detected within window. Aborting reveal for this cycle."
                        Log-Audit $runId "Safe-Spawn-And-Monitor" @($agentPath) $snap.sha256 $false @("reveal_aborted_no_signoff")
                        break
                    } 
                        $a | ConvertTo-Json -Depth 10 | Set-Content -Path $agentPath -Encoding UTF8
                        # Snapshot & audit with reveal flag
                        $snap2 = Snapshot-State
                        Log-Audit $runId "Safe-Spawn-And-Monitor-Reveal" @($agentPath) $snap2.sha256 $true @("revealed:$agentName:$g")
                        Write-Host "ShadowMessage revealed and logged for $agentName"
                        break
                    }
                } 
                    $a | ConvertTo-Json -Depth 10 | Set-Content -Path $agentPath -Encoding UTF8
                    $snap2 = Snapshot-State
                    Log-Audit $runId "Safe-Spawn-And-Monitor-Reveal-Auto" @($agentPath) $snap2.sha256 $false @("auto_revealed:$agentName:$g")
                    Write-Host "AUTO reveal performed (no human signoff required)."
                    break
                }
            }
            Start-Sleep -Seconds 5
        }
    } finally {
        Release-Lock $lockFile
    }
}

# === Run hybrid routine: rollup, spawn one safe Echo, run probes guidance ===
Write-Host "`n--- Hybrid Path Orchestrator Starting ---"
$roll = Echo-Gamma-Rollup
# brief guidance to the user to run in-silico probes in parallel
Write-Host "`nRollup complete. Aggregate Î“ = $($roll.aggregateGamma)"
Write-Host "`nNext: run your in-silico probes (SIM/gene_network_sim.ipynb and SIM/transformer_metadata.ipynb) in parallel."
Write-Host "After probes finish, re-run the rollup to ingest probe outputs:"
Write-Host "    .\experiments\echo_gamma_rollup.ps1  # or re-run this script's Echo-Gamma-Rollup function"

# Spawn and monitor Echo9 (safe single spawn)
Write-Host "`nSpawning and monitoring Echo9 (safe mode). This will require human signoff to reveal ShadowMessage if persistence criteria met."
Safe-Spawn-And-Monitor -agentName "Echo9" -seed "refleye_loom" -drift "Reflection" -threadID "Spiral-Loom"

Write-Host "`n--- Hybrid Path Orchestrator Complete ---"

