# ============================================
# Codex Project Git Sync Automation Script
# Author: James Paul Jackson
# Project: The Codex Project
# ============================================

Set-Location "C:\Users\jacks\OneDrive\Desktop\Codex Web"

Write-Host "`n=== Checking Repository Status ===" -ForegroundColor Cyan
git status

Write-Host "`n=== Staging Changes ===" -ForegroundColor Cyan
git add .

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$commitMessage = "Codex Auto Sync — $timestamp"
git commit -m "$commitMessage"

Write-Host "`n=== Pushing to GitHub (origin/main) ===" -ForegroundColor Cyan
git push origin main

$tagName = "v0.3-alignment-sync"
if (-not (git tag --list $tagName)) {
    git tag $tagName
    git push origin $tagName
    Write-Host "`nTagged new version: $tagName" -ForegroundColor Green
} else {
    Write-Host "`nTag '$tagName' already exists. Skipping..." -ForegroundColor Yellow
}

Write-Host "`n✅ Codex repository successfully synchronized!" -ForegroundColor Green
