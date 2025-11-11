try {
  if ($MyInvocation.MyCommand.Definition) {
    $content = $MyInvocation.MyCommand.Definition
    $content | Out-File -FilePath $DaemonPath -Encoding utf8 -Force
    Write-Host "[anchor] v2.2B-p1 daemon anchored => $DaemonPath"
  }
} catch { Write-Host "[anchor] skipped (running from file context)." }
