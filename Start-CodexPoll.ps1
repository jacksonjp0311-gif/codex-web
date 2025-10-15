function Start-CodexPoll {
  param(
    [string] $Path     = '.\codex_ledger.json',
    [int]    $Interval = 2
  )

  if (-not (Test-Path $Path)) {
    Write-Error "Ledger not found at $Path"
    return
  }

  $lastHash = (Get-FileHash $Path).Hash
  Write-Host "⏱️  Polling $Path every $Interval second(s)..."

  while ($true) {
    Start-Sleep -Seconds $Interval
    $newHash = (Get-FileHash $Path).Hash

    if ($newHash -ne $lastHash) {
      $lastHash = $newHash

      $stones = Get-Content $Path | ConvertFrom-Json
      $report = @{
        run_id        = [guid]::NewGuid().Guid
        timestamp     = (Get-Date).ToUniversalTime().ToString('o')
        state         = @{
          current_tip   = $stones[-1].digest
          ledger_length = $stones.Count
          errors        = @()
        }
        metrics       = @{ cycle_duration_ms = 0; health_score = 100 }
        last_feedback = @()
      }

      $json = $report | ConvertTo-Json -Depth 5
      $json | Set-Clipboard

      Write-Host "▶️  Codex event captured at $(Get-Date -Format o). Report copied to clipboard."
    }
  }
}
