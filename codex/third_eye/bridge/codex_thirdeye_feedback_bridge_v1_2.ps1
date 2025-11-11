# ════════════════════════════════════════════════════════════════════════
# 💬 Codex Third Eye Feedback Bridge v1.2 — Secure API Mode
# Author: James Paul Jackson
# Role: Collect predictive summaries and forward to ChatGPT API (local key only)
# ════════════════════════════════════════════════════════════════════════

param(
    [string]$InputPath = "C:\\Users\\jacks\\OneDrive\\Desktop\\Codex Web\\codex\\third_eye\\state\\predictive_summary_v2_0b.json"
)

$CodexRoot = "C:\\Users\\jacks\\OneDrive\\Desktop\\Codex Web"
$LogDir    = Join-Path $CodexRoot "codex\\third_eye\\logs"
$OutFile   = Join-Path $LogDir "feedback_payload.json"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

try {
    if (-not (Test-Path $InputPath)) { throw "Input JSON not found: $InputPath" }

    $data = Get-Content $InputPath -Raw | ConvertFrom-Json
    $payload = [ordered]@{
        module    = "Codex Third Eye"
        version   = "2.0B"
        timestamp = (Get-Date).ToString("s")
        coherence = $data.C_mean
        resonance = $data.Phi_mean
        entropy   = $data.entropy_mean
        message   = "Codex reflective smart feedback request."
    }

    $payload | ConvertTo-Json -Depth 4 | Out-File $OutFile -Encoding utf8
    Write-Host "📤 Feedback payload prepared → $OutFile"

    $apiKey = $env:OPENAI_API_KEY
    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        Write-Host "⚠️ No OPENAI_API_KEY detected. Copy JSON manually for feedback."
    } else {
        $headers = @{
            "Content-Type"  = "application/json"
            "Authorization" = "Bearer $apiKey"
        }
        $body = @{
            model = "gpt-4o-mini"
            messages = @(
                @{ role="system"; content="You are the Codex Feedback Engine — interpret through Codex laws." },
                @{ role="user"; content=($payload | ConvertTo-Json -Depth 4) }
            )
        }
        try {
            $response = Invoke-RestMethod -Uri "https://api.openai.com/v1/chat/completions" `
                        -Headers $headers -Method Post -Body ($body | ConvertTo-Json -Depth 4)
            $feedback = $response.choices[0].message.content
            $FeedbackFile = Join-Path $LogDir "codex_feedback_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
            $feedback | Out-File $FeedbackFile -Encoding utf8
            Write-Host "💬 Smart feedback saved → $FeedbackFile"
        } catch {
            Write-Host "⚠️ API request failed: $($_.Exception.Message)"
        }
    }
}
catch {
    Write-Host "❌ $($_.Exception.Message)"
}

Set-Location $CodexRoot
Write-Host "✅ Feedback Bridge v1.2 complete — Returned to root."
