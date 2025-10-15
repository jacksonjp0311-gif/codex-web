# Deploy-Dashboard.ps1

Push-Location (Resolve-Path .)

if (-not (Test-Path .\dashboard.py)) {
    Write-Error "dashboard.py not found. Aborting."
    Exit 1
}

# Write requirements.txt
@'
streamlit>=1.0
pandas
plotly
streamlit-autorefresh
'@ | Set-Content .\requirements.txt -Encoding UTF8

# Create .streamlit/config.toml
if (-not (Test-Path .\.streamlit)) {
    New-Item -ItemType Directory -Path .\.streamlit | Out-Null
}
@'
[server]
headless = true
enableCORS = false
port = 

[theme]
base = "dark"
primaryColor = "#1f77b4"
'@ | Set-Content .\.streamlit\config.toml -Encoding UTF8

# Stage and commit
git add .\dashboard.py, .\requirements.txt, .\.streamlit\config.toml

if (git diff --cached --quiet) {
    Write-Host "⏭ No changes to commit."
} else {
    git commit -m "🔮 Add dashboard and Streamlit Cloud config"
}

# Push and exit
git push origin main
Write-Host "✅ Pushed and triggered Streamlit Cloud rebuild."

Pop-Location
