<#
╔══════════════════════════════════════════════════════════════════════╗
║ 🜂  CODEX QIM v3.3A — 4D FIELD EVOLUTION (ALL-ONE WRAPPER)          ║
║ 🜁  Domain : Quantum Imaging • 4D ΔΦ (x,y,z,t) Field                ║
║ ∿   Law    : Anchor → Execute → State → Git → Return               ║
╚══════════════════════════════════════════════════════════════════════╝
#>

param(
    [string]$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web",
    [string]$QimRelPath  = "codex\quantum_imaging",
    [string]$AfmInputRel = "codex\quantum_imaging\input_afm\v3_3"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "🜂 QIM v3.3A • 4D Field Evolution (wrapper)"
Write-Host ""

Set-Location -Path $CodexRoot

$QimPath    = Join-Path $CodexRoot $QimRelPath
$EnginePath = Join-Path $QimPath "engine\codex_quantum_imaging_v3_3_field_4d_evolution.py"
$StateDir   = Join-Path $QimPath "state_v3_3"
$VisualsDir = Join-Path $QimPath "visuals_v3_3"
$InputPath  = Join-Path $CodexRoot $AfmInputRel

$dirs = @($QimPath, $StateDir, $VisualsDir, $InputPath)
foreach ($d in $dirs) {
    if (-not (Test-Path -LiteralPath $d)) {
        New-Item -ItemType Directory -Path $d | Out-Null
        Write-Host "🜁 Created directory: $d"
    }
}

if (-not (Test-Path -LiteralPath $EnginePath)) {
    Write-Host "⚠ Engine missing for QIM v3.3A: $EnginePath"
    return
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "🜁 Executing QIM v3.3A 4D Field Evolution engine..."

    $engineQuoted  = '"' + $EnginePath   + '"'
    $inputQuoted   = '"' + $InputPath    + '"'
    $stateQuoted   = '"' + $StateDir     + '"'
    $visualsQuoted = '"' + $VisualsDir   + '"'

    $argumentString = "$engineQuoted --input_dir $inputQuoted --state_dir $stateQuoted --visuals_dir $visualsQuoted"

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = $argumentString
    $psi.WorkingDirectory = $CodexRoot
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute        = $false
    $psi.CreateNoWindow         = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $null = $proc.Start()

    $stdOut = $proc.StandardOutput.ReadToEnd()
    $stdErr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()

    Write-Host $stdOut
    if ($stdErr.Trim().Length -gt 0) {
        Write-Host "⚠ Python stderr:"
        Write-Host $stdErr
    }

    $exitCode = $proc.ExitCode
    if ($exitCode -ne 0) {
        Write-Host "⚠ QIM v3.3A engine exited with code $exitCode. Skipping Git step."
    } else {
        Write-Host "🜂 QIM v3.3A run successful — proceeding to Git autosave."
        try {
            git add "codex/quantum_imaging" | Out-Null
            git commit -m "Codex QIM v3.3A — 4D Field Evolution run" | Out-Null
        } catch {}
        try {
            git push | Out-Null
            Write-Host "🜁 Git push complete — RootMirror sync requested."
        } catch {}
    }
}

Set-Location -Path $CodexRoot
Write-Host ""
Write-Host "∿ QIM v3.3A cycle complete — returned to root."
Write-Host ""
