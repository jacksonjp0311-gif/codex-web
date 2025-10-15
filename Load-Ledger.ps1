
# Load-Ledger.ps1

# 1) Path to your JSON-lines ledger
$path = 'codex_ledger.json'

# 2) Bail if missing
if (-not (Test-Path $path)) {
  Write-Host "❌ Missing file: $path" -ForegroundColor Red
  exit 1
}

# 3) Read raw text, strip BOM, drop blank lines
$raw   = Get-Content -Path $path -Raw -Encoding UTF8
$clean = $raw.TrimStart([char]0xFEFF) -split '\r?\n' | Where-Object { $_.Trim() -ne '' }

# 4) Parse only valid JSON-lines via one pipeline
$objects = $clean |
  ForEach-Object {
    try {
      ConvertFrom-Json -InputObject $_ -ErrorAction Stop
    } catch {
      Write-Host "🔶 Dropped invalid JSON line:`n$_" -ForegroundColor DarkYellow
    }
  }

# 5) Rewrite ledger with only compressed, valid JSON-lines
$objects |
  ForEach-Object { $_ | ConvertTo-Json -Compress } |
  Set-Content -Path $path -Encoding UTF8

# 6) Report & preview
Write-Host "✅ Cleaned ledger: $($objects.Count) valid lines" -ForegroundColor Green

if ($objects.Count -gt 0) {
  Write-Host "`n🔍 First 5 entries:" -ForegroundColor Cyan
  $objects | Select-Object -First 5 | Format-Table -AutoSize
}
