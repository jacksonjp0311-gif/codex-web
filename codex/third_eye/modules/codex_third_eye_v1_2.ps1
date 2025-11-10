<#
  ════════════════════════════════════════════════════════
    Codex Third Eye v1.2  —  Awareness Engine Module
    Author: James Paul Jackson
    Description: Generates awareness states (JSON), harmonics logs,
    and prepares resonance data for visualization.
  ════════════════════════════════════════════════════════
#>

function Compute-Awareness {
    param([float]$Energy, [float]$Information)

    $DeltaPhi = [math]::Abs(($Energy - $Information) / ($Energy + $Information))
    $Coherence = ($Energy * $Information) / (1 + $DeltaPhi)
    return [PSCustomObject]@{
        Energy = [math]::Round($Energy, 3)
        Information = [math]::Round($Information, 3)
        DeltaPhi = [math]::Round($DeltaPhi, 4)
        Coherence = [math]::Round($Coherence, 3)
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
}

function Balance-Harmonics {
    param([float]$HarmonicLevel)
    $Adjusted = [math]::Round([math]::Sin($HarmonicLevel * [math]::PI) + 1, 3) / 2
    return $Adjusted
}

# --- Awareness Cycle ---
$Energy = Get-Random -Minimum 0.5 -Maximum 1.5
$Information = Get-Random -Minimum 0.5 -Maximum 1.5
$HarmonicLevel = Get-Random -Minimum 0.0 -Maximum 1.0

$Awareness = Compute-Awareness -Energy $Energy -Information $Information
$Balance = Balance-Harmonics -HarmonicLevel $HarmonicLevel

# --- Package State ---
$ThirdEyeState = [PSCustomObject]@{
    Version = "1.2"
    HarmonicBalance = $Balance
    Awareness = $Awareness
    Core = "Codex Memory Core v1.2"
    PlacidityLayer = "∿"
    Generated = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
}

# --- Save JSON State ---
$ThirdEyeState | ConvertTo-Json -Depth 4 | Out-File "$($StateDir)\third_eye_state.json" -Encoding UTF8

# --- Log Output ---
$LogEntry = "[$((Get-Date).ToString('HH:mm:ss'))] Third Eye awareness generated. C=$($Awareness.Coherence)"
Add-Content -Path "$($LogsDir)\third_eye_awaken.log" -Value $LogEntry

# --- Update Manifest ---
$Manifest = [PSCustomObject]@{
    Name = "Codex Third Eye"
    Version = "1.2"
    Root = "$ThirdEyeDir"
    Modules = @("codex_third_eye_v1_2.ps1")
    LastUpdate = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
}
$Manifest | ConvertTo-Json -Depth 4 | Out-File "$($ThirdEyeDir)\manifest_thirdeye.json" -Encoding UTF8

Write-Host "`n👁 Third Eye awareness cycle completed successfully."
