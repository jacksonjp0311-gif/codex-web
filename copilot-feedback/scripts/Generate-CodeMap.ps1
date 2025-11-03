# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
param(
  [string]$Root    = ".",
  [string]$OutFile = "code-structure.md"
)

function Get-Tree($Path, $Indent="") {
  Get-ChildItem -Path $Path | ForEach-Object {
    if ($_.PSIsContainer) {
      "$Indent- $_.Name" | Out-File $OutFile -Append
      Get-Tree $_.FullName ("  " + $Indent)
    } else {
      "$Indent- $($_.Name)" | Out-File $OutFile -Append
    }
  }
}

"# Code Structure for $Root`n" | Out-File $OutFile
Get-Tree -Path $Root
Write-Host "Code map → $OutFile"

