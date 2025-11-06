try {
    $root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
    $codexDir = "$root\codex"
    $automationDir = "$codexDir\automation"
    $handoffDir = "$codexDir\handoff"
    $evolutionDir = "$codexDir\evolution"
    $archiveDir = "$codexDir\archive"
    $kernelDir = "$codexDir\core\kernel"

    # Ensure directories exist
    foreach ($dir in @($automationDir, $handoffDir, $evolutionDir, $archiveDir, $kernelDir)) {
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    }

    # Anchor script in automation folder
    $scriptPath = "$automationDir\codex_reorganize_root_v3_8.ps1"
    if ($MyInvocation.MyCommand.Path) {
        Copy-Item -Path $MyInvocation.MyCommand.Path -Destination $scriptPath -Force
    } else {
        $content = $MyInvocation.MyCommand.Definition
        $content | Out-File -Encoding utf8 $scriptPath
    }
    Write-Host "🪶 Reorganization script anchored at $scriptPath`n"

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $logPath = "$handoffDir\codex_reorg_log_v3_8_$timestamp.txt"
    Write-Host "📦 Starting root cleanup and file relocation...`n"
    Add-Content -Path $logPath -Value "=== Codex Root Reorganization Log — $timestamp ===`n"

    # --- Move Evolution/Handoff/Versioned Files ---
    Get-ChildItem $root -File | Where-Object {
        $_.Name -match "v\d+" -or $_.Name -match "handoff" -or $_.Extension -eq ".log"
    } | ForEach-Object {
        Move-Item -Path $_.FullName -Destination $evolutionDir -Force
        Add-Content -Path $logPath -Value "Moved evolution file: $($_.Name)"
    }

    # --- Move Kernel Files ---
    Get-ChildItem $root -Directory | Where-Object { $_.Name -like "jackson_os_kernel*" } | ForEach-Object {
        Move-Item -Path $_.FullName -Destination $kernelDir -Force
        Add-Content -Path $logPath -Value "Moved kernel folder: $($_.Name)"
    }

    # --- Move PowerShell Utilities ---
    Get-ChildItem $root -File -Filter "*.ps1" | Where-Object {
        $_.Name -notlike "codex_sync.ps1" -and $_.Name -notlike "codex_auto_cycle*"
    } | ForEach-Object {
        Move-Item -Path $_.FullName -Destination $automationDir -Force
        Add-Content -Path $logPath -Value "Moved automation script: $($_.Name)"
    }

    # --- Move Logs and Backups ---
    Get-ChildItem $root -File | Where-Object {
        $_.Extension -in @(".bak", ".csv", ".txt") -and $_.Name -notlike "README*"
    } | ForEach-Object {
        Move-Item -Path $_.FullName -Destination $archiveDir -Force
        Add-Content -Path $logPath -Value "Archived: $($_.Name)"
    }

    # --- Final Root Cleanup ---
    $preserve = @("README.md", "CodexChronicle.md", ".gitignore", "CodexMap.txt", "ALIGNMENT.md")
    Get-ChildItem $root -File | Where-Object { $preserve -notcontains $_.Name } | ForEach-Object {
        Add-Content -Path $logPath -Value "Keeping in root: $($_.Name)"
    }

    Write-Host "`n✅ Codex root reorganization complete."
    Write-Host "📜 Log saved to: $logPath"
    Set-Location $root
    Write-Host "🏁 Returned to Codex root: $root"
}
catch {
    Write-Host "⚠️ Error during reorganization: $_" -ForegroundColor Red
}
