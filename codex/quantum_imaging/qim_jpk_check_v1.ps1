param(
    [string]$SourceAFM = "C:\Users\jacks\OneDrive\Desktop\AFM images roughness"
)

$ErrorActionPreference = "Stop"

$Root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
Set-Location $Root

$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
$GitCmd    = Get-Command git    -ErrorAction SilentlyContinue

$QIMRoot  = Join-Path $Root "codex\quantum_imaging"
$LogsDir  = Join-Path $QIMRoot "logs_jpk_check"
$StateDir = Join-Path $QIMRoot "state_jpk_check"

foreach ($d in @($LogsDir, $StateDir)) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d | Out-Null
    }
}

$PyEngine = Join-Path $QIMRoot "engine_jpk_check_v1_0.py"

python $PyEngine "$SourceAFM" "$LogsDir" "$StateDir"
$exit = $LASTEXITCODE

if ($GitCmd) {
    git add "codex/quantum_imaging" | Out-Null
    git commit -m "QIM JPK Format Check v1.0" | Out-Null
    git pull --rebase | Out-Null
    git push | Out-Null
}

Set-Location $Root
