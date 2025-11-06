try {
    # --- Root and Timestamp Setup ---
    $root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
    Set-Location $root
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

    # --- Paths ---
    $handoffDir = "$root\codex\handoff"
    New-Item -ItemType Directory -Force -Path $handoffDir | Out-Null

    $manifestPath = "$handoffDir\handoff_state_v3_8_$timestamp.json"
    $dumpPath     = "$handoffDir\codex_full_dump_$timestamp.txt"
    $mapPath      = "$handoffDir\dump_mapping_v3_8_$timestamp.csv"
    $progressPath = "$handoffDir\codex_manifest_progress_$timestamp.json"
    $scriptPath   = "$handoffDir\codex_handoff_v3_8.ps1"

    # --- Anchor Script (safe for console or file execution) ---
    if ($MyInvocation.MyCommand.Path) {
        $scriptContent = Get-Content -Raw $MyInvocation.MyCommand.Path
    } else {
        $scriptContent = $MyInvocation.MyCommand.Definition
    }
    $scriptContent | Out-File -Encoding utf8 $scriptPath
    Write-Host "🪶 Script anchored at $scriptPath`n"

    # --- Start Tracking ---
    $startTime = Get-Date
    Write-Host "🔹 Initiating Codex v3.8 Unified Visibility Handoff" -ForegroundColor Cyan

    # ============================================================
    # 1️⃣ Layer One — Manifest
    # ============================================================
    Write-Host "📦 Building Manifest Layer..."
    $manifest = [ordered]@{
        version = "v3.8"
        timestamp = $timestamp
        author = "James Paul Jackson"
        project = "The Codex Project"
        codex_root = $root
        layers = @{
            manifest = $manifestPath
            source = $dumpPath
            mapping = $mapPath
        }
        files = @()
    }

    $allFiles = Get-ChildItem -Path $root -Recurse -File
    $total = $allFiles.Count
    $counter = 0

    foreach ($file in $allFiles) {
        $counter++
        if ($counter % 500 -eq 0) {
            $elapsed = (Get-Date) - $startTime
            $pct = [math]::Round(($counter / $total) * 100, 2)
            Write-Host "   ⏳ Manifest progress: $pct% ($counter / $total) [$($elapsed.ToString("hh\:mm\:ss"))]"
        }

        $relativePath = $file.FullName.Substring($root.Length + 1)
        $manifest.files += [ordered]@{
            path = $relativePath
            size = $file.Length
            modified = $file.LastWriteTime
            hash = (Get-FileHash $file.FullName -Algorithm SHA256).Hash
        }
    }

    $manifest | ConvertTo-Json -Depth 8 | Out-File -Encoding utf8 $manifestPath

    # Save progress snapshot
    $duration = (Get-Date) - $startTime
    $progressReport = @{
        total_files = $total
        processed = $counter
        duration = $duration.ToString("hh\:mm\:ss")
        output = $manifestPath
    }
    $progressReport | ConvertTo-Json -Depth 8 | Out-File -Encoding utf8 $progressPath
    Write-Host "✅ Manifest completed. Files processed: $total | Duration: $($duration.ToString("hh\:mm\:ss"))"

    # ============================================================
    # 2️⃣ Layer Two — Full Source Dump
    # ============================================================
    Write-Host "📜 Generating Full Source Dump..."
    foreach ($file in $allFiles) {
        "`n# --- $($file.FullName.Replace($root, '').TrimStart('\')) ---" | Out-File -Append -Encoding utf8 $dumpPath
        Get-Content $file.FullName | Out-File -Append -Encoding utf8 $dumpPath
    }

    # ============================================================
    # 3️⃣ Layer Three — Mapping
    # ============================================================
    Write-Host "🧭 Creating Mapping Layer..."
    "file_path,extension,size,modified" | Out-File -Encoding utf8 $mapPath
    foreach ($file in $allFiles) {
        "$($file.FullName.Replace($root, '').TrimStart('\')),$($file.Extension),$($file.Length),$($file.LastWriteTime)" | Out-File -Append -Encoding utf8 $mapPath
    }

    # ============================================================
    # 4️⃣ Git Commit + Push
    # ============================================================
    Write-Host "🌐 Committing and pushing to GitHub..."
    git add -A
    $commitMsg = "🪶 Codex v3.8 — Anchored Unified Visibility Handoff | $timestamp"
    git commit -m $commitMsg 2>$null
    git push origin main 2>$null

    # ============================================================
    # ✅ Completion
    # ============================================================
    $totalDuration = (Get-Date) - $startTime
    Write-Host "`n✅ Codex v3.8 Handoff complete."
    Write-Host "   Manifest: $manifestPath"
    Write-Host "   Source Dump: $dumpPath"
    Write-Host "   Mapping: $mapPath"
    Write-Host "   Total Time: $($totalDuration.ToString("hh\:mm\:ss"))"
}
catch {
    Write-Host "⚠️ Error encountered: $_" -ForegroundColor Red
}
