# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
Describe "Codex Ledger Schema" {
  It "parses every line as valid JSON" {
    $errs = 0
    Get-Content codex_ledger.json | ForEach-Object {
      try { $_ | ConvertFrom-Json } catch { $errs++; break }
    }
    $errs | Should Be 0
  }
}

