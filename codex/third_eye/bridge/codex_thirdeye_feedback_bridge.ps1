# ════════════════════════════════════════════════════════════════════════
# 🧿 Codex Third Eye Feedback Bridge — Secure Mode
# Collects predictive summaries and optionally posts them to ChatGPT API.
# Uses local environment key: OPENAI_API_KEY (never logged or stored)
# ════════════════════════════════════════════════════════════════════════

param(
  [string] \ = "C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\third_eye\state\predictive_summary_v2_0b.json"
)

\C:\Users\jacks\OneDrive\Desktop\Codex Web = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
\   = Join-Path \C:\Users\jacks\OneDrive\Desktop\Codex Web "codex\third_eye\logs\feedback_payload.json"

try {
    if (-not (Test-Path \)) { throw "Input JSON not found: \" }

    # Load predictive summary
    \ = Get-Content \ -Raw | ConvertFrom-Json

    # Build compact feedback payload
    \ = [ordered]@{
        module    = "Codex Third Eye"
        version   = "2.0B"
        timestamp = (Get-Date).ToString("s")
        coherence = \.C_mean
        resonance = \.Phi_mean
        entropy   = \.entropy_mean
        message   = "Codex smart feedback request — symbolic + numerical insights."
    }

    # Write to file for manual paste or review
    \ | ConvertTo-Json -Depth 4 | Out-File \ -Encoding utf8
    Write-Host "📤 Feedback payload prepared → \"

    # --- Secure API call (optional) ---
    \ = \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
    if ([string]::IsNullOrWhiteSpace(\)) {
        Write-Host "⚠️ No OPENAI_API_KEY detected. Copy JSON manually for feedback."
    } else {
        \ = @{
            "Content-Type"  = "application/json"
            "Authorization" = "Bearer \"
        }

        \ = @{
            model = "gpt-4o-mini"
            messages = @(@{
                role = "system"
                content = "You are the Codex Feedback Engine — interpret data through the Codex Memory Core laws."
            }, @{
                role = "user"
                content = (\ | ConvertTo-Json -Depth 4)
            })
        }

        try {
            \ = Invoke-RestMethod -Uri "https://api.openai.com/v1/chat/completions" 
                        -Headers \ -Method Post -Body (\ | ConvertTo-Json -Depth 4)
            \ = \.choices[0].message.content
            \ = Join-Path \C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\third_eye\logs "codex_feedback_20251111_073532.txt"
            \ | Out-File \ -Encoding utf8
            Write-Host "💬 Smart feedback saved → \"
        } catch {
            Write-Host "⚠️ API request failed: \"
        }
    }

} catch {
    Write-Host "❌ \"
} finally {
    try { Set-Location \C:\Users\jacks\OneDrive\Desktop\Codex Web } catch {}
    Write-Host "
🏁 Returned to Codex root: \C:\Users\jacks\OneDrive\Desktop\Codex Web"
}
