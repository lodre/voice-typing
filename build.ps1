# Сборка переносимой папки dist\VoiceTyping: exe + модель + README
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

.\.venv\Scripts\python.exe -m PyInstaller VoiceTyping.spec --noconfirm --log-level WARN
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

robocopy "models" "dist\VoiceTyping\models" /E /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed" }
$global:LASTEXITCODE = 0

Copy-Item "README.md" "dist\VoiceTyping\" -Force

Write-Host "Готово: dist\VoiceTyping (скопируйте папку целиком на другой ПК)"
