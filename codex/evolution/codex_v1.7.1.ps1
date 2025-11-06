$ErrorActionPreference = "Stop"
$root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$kernelDir = Join-Path $root "jackson_os_kernel"
$tracker = Join-Path $root "codex_kernel_goal_tracker.md"
Set-Location $root
Write-Host "[codex v1.7.1] ♾️ Live Continuity Loop active on: $kernelDir"
Write-Host "[codex v1.7.1] Press Ctrl+C to stop."
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $kernelDir
$watcher.Filter = "*.py"
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true
$action = {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $file = $Event.SourceEventArgs.FullPath
    $type = $Event.SourceEventArgs.ChangeType
    Add-Content -Path $tracker -Value "`r`n### Live Kernel Update — $ts`r`n- File: $file`r`n- Type: $type`r`n" -Encoding UTF8
    try {
        Set-Location $root
        git add -A
        git commit -m "[codex] ♾️ Live Continuity Sync — $ts"
        git tag -a ("CODEX-KERNEL-LIVE-v1.7.1-" + (Get-Date).ToString("yyyyMMdd-HHmmss")) -m "Codex Live Auto-Commit"
        git push origin main
        git push origin --tags
        Write-Host "[codex v1.7.1] 🔁 Synced live kernel change: $file"
    } catch { Write-Host "[codex v1.7.1] ⚠️ Commit skipped: $($_.Exception.Message)" }
}
Register-ObjectEvent $watcher "Changed" -Action $action | Out-Null
Register-ObjectEvent $watcher "Created" -Action $action | Out-Null
Register-ObjectEvent $watcher "Deleted" -Action $action | Out-Null
Register-ObjectEvent $watcher "Renamed" -Action $action | Out-Null
while ($true) { Start-Sleep -Seconds 60 }
