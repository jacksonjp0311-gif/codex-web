try {
    $root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
    $automationDir = "$root\codex\automation"
    $handoffDir = "$root\codex\handoff"
    Set-Location $root

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $scriptPath = "$automationDir\codex_extract_summary_v3_8.ps1"
    if ($MyInvocation.MyCommand.Path) {
        $scriptContent = Get-Content -Raw $MyInvocation.MyCommand.Path
    } 
    $scriptContent | Out-File -Encoding utf8 $scriptPath
    Write-Host "🪶 Summary Extractor anchored at $scriptPath`n"

    # --- Locate Latest Artifact Index ---
    $latestIndex = Get-ChildItem -Path $handoffDir -Filter "codex_artifact_index_v3_8_*.json" |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latestIndex) { throw "No artifact index found. Run codex_artifact_indexer.ps1 first." }

    Write-Host "📄 Reading artifact index: $($latestIndex.FullName)"
    $data = Get-Content -Raw $latestIndex.FullName | ConvertFrom-Json

    $versions = @()
    $metricsList = @()
    foreach ($a in $data.artifacts) {
        if ($a.version) { $versions += $a.version }
        if ($a.metrics) { $metricsList += $a.metrics }
    }

    # --- Compute Aggregate Metrics ---
    $allCII  = @($metricsList | ForEach-Object { $_.CII })  | Where-Object { $_ -ne $null }
    $allHphi = @($metricsList | ForEach-Object { $_.Hphi }) | Where-Object { $_ -ne $null }
    $allRMI  = @($metricsList | ForEach-Object { $_.RMI })  | Where-Object { $_ -ne $null }

    function Mean($arr) { if ($arr.Count -gt 0) { ($arr | Measure-Object -Average).Average }  }

    # --- Compute Metric Spread ---
    function MetricSpread($arr) {
        if ($arr.Count -eq 0) { return @{ max = 0; min = 0 } }
        $max = ($arr | Measure-Object -Maximum).Maximum
        $min = ($arr | Measure-Object -Minimum).Minimum
        return @{ max = [math]::Round($max, 6); min = [math]::Round($min, 6) }
    }

    $summary = [ordered]@{
        codex_version = "v3.8"
        timestamp = $timestamp
        total_artifacts = $data.total_artifacts
        unique_versions = ($versions | Sort-Object -Unique)
        metrics_mean = @{
            CII  = [math]::Round((Mean $allCII), 6)
            Hphi = [math]::Round((Mean $allHphi), 6)
            RMI  = [math]::Round((Mean $allRMI), 6)
        }
        metrics_spread = @{
            CII  = (MetricSpread $allCII)
            Hphi = (MetricSpread $allHphi)
            RMI  = (MetricSpread $allRMI)
        }
        generated_from = $latestIndex.Name
    }

    $summaryPath = "$handoffDir\codex_summary_v3_8_$timestamp.json"
    $summary | ConvertTo-Json -Depth 8 | Out-File -Encoding utf8 $summaryPath

    Write-Host "✅ Codex summary generated: $summaryPath"
    Set-Location $root
}
catch {
    Write-Host "⚠️ Error in Summary Extractor: $_" -ForegroundColor Red
}

