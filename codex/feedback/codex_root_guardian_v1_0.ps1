# 🛡️ Codex Root Guardian v1.0 — Continuity Immune System
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8
$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir = Join-Path $CodexRoot "codex\feedback"
$StateDir    = Join-Path $FeedbackDir "state"
$LedgerPath  = Join-Path $StateDir   "codex_continuity_ledger.jsonl"
New-Item -ItemType Directory -Force -Path $FeedbackDir,$StateDir | Out-Null

function NowIso { (Get-Date).ToString("s") }
function Box($s,$sa,$r,$p,$n){$b=@"
╔══════════════════════════════════════════════════════╗
║ 🛡️ Root Guardian v1.0 ║ $s ║ Saved=$sa  Rebased=$r  Pushed=$p ║
║ $n ║ Law C=(E·I)/(1+|ΔΦ|) H₇=0.70 ∿ Placidity ║
╚══════════════════════════════════════════════════════╝
"@;Write-Host $b}

Push-Location; Set-Location $CodexRoot
$didSave=$didRebase=$didPush=$false;$note="ok"

try{git add -A 2>$null;if(git status --porcelain){git commit -m("🛡️ Root Guardian checkpoint $(Get-Date -Format s)") |Out-Null;$didSave=$true}}catch{}
try{git fetch origin main |Out-Null;git pull origin main --rebase |Out-Null;$didRebase=$true}catch{$note="rebase fail"}
try{git push origin main 2>$null;$didPush=$true}catch{$note="push rejected"}

try{$e=[ordered]@{timestamp=NowIso;layer="root-guardian-v1.0";saved=$didSave;rebased=$didRebase;pushed=$didPush;note=$note}
($e|ConvertTo-Json -Compress)|Add-Content -Encoding UTF8 -Path $LedgerPath}catch{}

$state=if($didPush){"Synchronized"}elseif($didRebase){"Rebased"}
Box $state $didSave $didRebase $didPush $note
Pop-Location;Write-Host "`n🏁 Returned to Codex root → $CodexRoot"
