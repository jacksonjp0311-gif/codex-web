try {
    $root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
    $handoffDir = "$root\codex\handoff"
    Set-Location $root

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $scriptPath = "$root\codex\automation\codex_self_reference_injector_v3_8.ps1"
    if ($MyInvocation.MyCommand.Path) {
        $scriptContent = Get-Content -Raw $MyInvocation.MyCommand.Path
    } else {
        $scriptContent = $MyInvocation.MyCommand.Definition
    }
    $scriptContent | Out-File -Encoding utf8 $scriptPath
    Write-Host "🪶 Self-Reference Injector anchored at $scriptPath`n"

    # --- Locate latest manifest, artifact index, and summary ---
    $latestManifest = Get-ChildItem -Path $handoffDir -Filter "handoff_state_v3_8_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $latestIndex = Get-ChildItem -Path $handoffDir -Filter "codex_artifact_index_v3_8_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $latestSummary = Get-ChildItem -Path $handoffDir -Filter "codex_summary_v3_8_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if (-not $latestManifest -or -not $latestSummary -or -not $latestIndex) {
        throw "Missing one or more required files (manifest, summary, index)."
    }

    Write-Host "🔗 Linking:"
    Write-Host "   Manifest: $($latestManifest.Name)"
    Write-Host "   Index:    $($latestIndex.Name)"
    Write-Host "   Summary:  $($latestSummary.Name)"

    # --- Load manifest and update references ---
    $manifest = Get-Content -Raw $latestManifest.FullName | ConvertFrom-Json
    if (-not $manifest.meta) { $manifest | Add-Member -MemberType NoteProperty -Name meta -Value @{} }

    $manifest.meta.summary_link = $latestSummary.Name
    $manifest.meta.artifact_index = $latestIndex.Name
    $manifest.meta.self_reference_timestamp = $timestamp

    # --- Save updated manifest ---
    $linkedManifestPath = "$handoffDir\handoff_state_v3_8_linked_$timestamp.json"
    $manifest | ConvertTo-Json -Depth 12 | Out-File -Encoding utf8 $linkedManifestPath

    Write-Host "✅ Self-reference injected successfully."
    Write-Host "📁 Updated manifest saved as: $linkedManifestPath"

    Set-Location $root
}
catch {
    Write-Host "⚠️ Error in Self-Reference Injector: $_" -ForegroundColor Red
}
