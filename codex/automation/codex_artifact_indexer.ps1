try {
    # --- Root Paths ---
    $root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
    $automationDir = "$root\codex\automation"
    $handoffDir = "$root\codex\handoff"
    Set-Location $root

    # --- Timestamp + Anchor ---
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $scriptPath = "$automationDir\codex_artifact_indexer.ps1"
    if ($MyInvocation.MyCommand.Path) {
        $scriptContent = Get-Content -Raw $MyInvocation.MyCommand.Path
    } 
    $scriptContent | Out-File -Encoding utf8 $scriptPath
    Write-Host "🪶 Artifact Indexer anchored at $scriptPath`n"

    # --- Output Path ---
    $indexPath = "$handoffDir\codex_artifact_index_v3_8_$timestamp.json"

    # --- Discover Artifacts ---
    Write-Host "🔎 Scanning for Codex artifacts..."
    $jsonFiles = Get-ChildItem -Path $root -Recurse -Filter *.json
    $artifacts = @()

    foreach ($file in $jsonFiles) {
        try {
            $data = Get-Content -Raw $file.FullName | ConvertFrom-Json -ErrorAction Stop
            if ($data.version -and $data.metrics) {
                $artifact = [ordered]@{
                    file = $file.FullName.Substring($root.Length + 1)
                    version = $data.version
                    type = $data.type
                    timestamp = $data.timestamp
                    metrics = $data.metrics
                    size = $file.Length
                    modified = $file.LastWriteTime
                }
                $artifacts += $artifact
            }
        } catch {
            # Ignore non-Codex or malformed JSON
        }
    }

    # --- Save Index ---
    $index = [ordered]@{
        codex_version = "v3.8"
        total_artifacts = $artifacts.Count
        timestamp = $timestamp
        artifacts = $artifacts
    }

    $index | ConvertTo-Json -Depth 8 | Out-File -Encoding utf8 $indexPath
    Write-Host "✅ Artifact index created: $indexPath"
    Write-Host "   Total artifacts indexed: $($artifacts.Count)"

    # --- Return to Root ---
    Set-Location $root
}
catch {
    Write-Host "⚠️ Error in Artifact Indexer: $_" -ForegroundColor Red
}

