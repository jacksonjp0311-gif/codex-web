param(
    [string]$Intent = "giza_v6_21_oracle_syntax_engine"
)

$ErrorActionPreference = "Stop"

$root = Split-Path $MyInvocation.MyCommand.Path -Parent
$root = Split-Path $root -Parent   # visuals\giza → web\visuals
$codexRoot = Split-Path $root -Parent

$gizaDir  = Join-Path $codexRoot "web\visuals\giza"
$stateDir = Join-Path $gizaDir "state"

if (-not (Test-Path $stateDir)) {
    New-Item -ItemType Directory -Path $stateDir | Out-Null
}

$timestamp = (Get-Date).ToUniversalTime().ToString("o")

# simple synthetic ΔΦ signature for GIZA mini-engine
$E = 0.15
$I = 0.002
$deltaPhi = 0.314
$Craw = ($E * $I) / (1 + [math]::Abs($deltaPhi))
$C = [math]::Round($Craw, 6)

$state = @{
    module    = "Codex GIZA v6.21 — Oracle Syntax (mini)"
    version   = "6.21-mini"
    intent    = $Intent
    timestamp = $timestamp
    triad     = @{
        E          = $E
        I          = $I
        C          = $C
        H7         = 0.70
        placidity  = "∿"
        delta_phi  = $deltaPhi
        glyph_sig  = "🜂🜁🜄∿"
    }
}

$statePath = Join-Path $stateDir "giza_v6_21_state.json"
($state | ConvertTo-Json -Depth 10) | Set-Content -Path $statePath -Encoding UTF8

Write-Host "[GIZA v6.21 mini] State written → $statePath"
