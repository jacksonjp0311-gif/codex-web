function Subscribe-CodexEvent {
  param([string] $LedgerPath = '.\codex_ledger.json')

  $watcher = New-Object System.IO.FileSystemWatcher
  $watcher.Path         = Split-Path $LedgerPath
  $watcher.Filter       = Split-Path $LedgerPath -Leaf
  $watcher.NotifyFilter = [IO.NotifyFilters]::LastWrite

  Register-ObjectEvent $watcher Changed -SourceIdentifier CodexLedgerChanged -Action {
    $report = @{
      run_id        = [guid]::NewGuid().Guid
      timestamp     = (Get-Date).ToUniversalTime().ToString('o')
      state         = @{
        current_tip   = (Get-Content $LedgerPath | ConvertFrom-Json)[-1].digest
        ledger_length = (Get-Content $LedgerPath | ConvertFrom-Json).Count
        errors        = @()
      }
      metrics       = @{ cycle_duration_ms = 0; health_score = 100 }
      last_feedback = @()
    }
    $json = Format-CodexReport -Report $report
    Copy-ToClipboard -Text $json
    Write-Host "▶️  Codex event captured. Report copied to clipboard."
  }

  $watcher.EnableRaisingEvents = $true
  Write-Host "🛰️  Subscribed to $LedgerPath changes."
}

function Format-CodexReport {
  param([hashtable] $Report)
  return $Report | ConvertTo-Json -Depth 5
}

function Copy-ToClipboard {
  param([string] $Text)
  $Text | Set-Clipboard
  Write-Host "📋  Copied $($Text.Length) chars to clipboard."
}

function Apply-Recommendations {
  param([string] $RecoJsonPath)
  $reco = Get-Content $RecoJsonPath | ConvertFrom-Json
  foreach($fix in $reco.prioritized_fixes) {
    Write-Host "🔨 Applying $($fix.id): $($fix.description)"
    Invoke-Expression $fix.command
  }
  Log-FeedbackEntry -Entry $reco
}

function Log-FeedbackEntry {
  param([psobject] $Entry)
  $path = '.\feedback_ledger.json'
  if(-not (Test-Path $path)) { '[]' | Out-File $path -Encoding utf8 }
  $feed = Get-Content $path | ConvertFrom-Json
  $feed += $Entry
  $feed | ConvertTo-Json -Depth 5 | Out-File $path -Encoding utf8
  Write-Host "🗒️  Logged feedback entry. Total: $($feed.Count)"
}
