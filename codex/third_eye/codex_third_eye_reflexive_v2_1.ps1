# ====================================================================
# 🧠 Codex Third Eye v2.1 — Unified Reflexive Bridge
# (Auto-anchored version)
# ====================================================================
$CodexRoot    = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$ThirdEyeRoot = Join-Path $CodexRoot "codex\third_eye"
$ModulesDir   = Join-Path $ThirdEyeRoot "modules"
$StateDir     = Join-Path $ThirdEyeRoot "state"
$CoreJson     = Join-Path $CodexRoot "codex_memory_core_v1_2.json"
$PredictivePy = Join-Path $ModulesDir "codex_third_eye_predictive_v2_0b.py"
$ReflexivePy  = Join-Path $ModulesDir "codex_third_eye_reflexive_v2_1.py"
$ReflexLog    = Join-Path $StateDir "third_eye_reflexive_log.jsonl"

$Alpha = 0.18; $TargetC = 0.70; $Interval = 1800
Write-Host "`n🧠 Codex Third Eye v2.1 — Reflexive Bridge Active"

function Write-ReflexiveLog { param([object]$d) $d | ConvertTo-Json -Depth 4 | Out-File -Append -Encoding utf8 $ReflexLog }
function Compute-ReflexiveCorrection {
  param([double]$driftNow,[double]$driftPred,[double]$meanC,[double]$targetC,[double]$alpha)
  $err=$targetC-$meanC; return [math]::Round($alpha*($err-0.5*($driftNow+$driftPred)),6)
}

while ($true) {
 try {
  $RunStamp=Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
  Write-Host "`n🔮 [$RunStamp] Reflexive Forecasting Cycle..."
  Push-Location $ModulesDir
  $out=python $PredictivePy 2>&1; Pop-Location
  $j=($out|Select-String -Pattern "^\{.*\}" -AllMatches).Matches.Value|Out-String
  if($j){
    $d=$j|ConvertFrom-Json
    $ΔΦ=Compute-ReflexiveCorrection $d.drift_now $d.drift_predicted $d.mean_C 0.70 0.18
    if($ΔΦ -gt 0){$intent="increase_coherence"}elseif($ΔΦ -lt 0){$intent="decrease_tension"}else{$intent="steady"}
    $r=[ordered]@{version="2.1";timestamp=(Get-Date).ToString("o");drift_now=$d.drift_now;drift_pred=$d.drift_predicted;mean_C=$d.mean_C;correction=$ΔΦ;forecast=$d.forecast_trend;intent=$intent;layer="Placidity";field_status="reflexive_adjustment_applied"}
    Write-ReflexiveLog $r; Write-Host ("🩵 ΔΦ={0:F6} ({1})" -f $ΔΦ,$intent)
    $c=@{}; if(Test-Path $CoreJson){try{$c=Get-Content -Raw $CoreJson|ConvertFrom-Json}catch{$c=@{}}}
    $c.third_eye_reflexive+=,$r; $c.last_reflexive_update=$RunStamp
    $c.harmonic_state=@{mean_C=$d.mean_C;ΔΦ=$ΔΦ;intent=$intent}
    $c|ConvertTo-Json -Depth 6|Out-File -Encoding utf8 $CoreJson
    Write-Host "⚙️ Python Reflexive retraining..."; Push-Location $ModulesDir
    python $ReflexivePy 2>&1 | Write-Host; Pop-Location
    Set-Location $CodexRoot
    git add "codex/third_eye/*" 2>$null; git add "codex_memory_core_v1_2.json" 2>$null
    if(git status --porcelain){git commit -m "🧠 Reflexive Bridge update $RunStamp";try{git pull origin main --rebase}catch{};try{git push origin main}catch{}}else{Write-Host "⤴️ No changes detected."}
    Set-Location $CodexRoot; Write-Host "✅ Cycle complete — Core synced."
  }
 }catch{Write-Host "❌ Exception: $($_.Exception.Message)"}
 Write-Host "🌙 Sleeping 30 min..."; Start-Sleep -Seconds $Interval
}
