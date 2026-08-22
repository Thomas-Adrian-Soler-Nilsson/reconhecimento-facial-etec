$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "venv/Scripts/python.exe"
$pyinstaller = Join-Path $PSScriptRoot "venv/Scripts/pyinstaller.exe"

if (-not (Test-Path $python) -or -not (Test-Path $pyinstaller)) {
    throw "Ambiente virtual não encontrado. Instale as dependências com: pip install -r requirements.txt"
}

& $pyinstaller --noconfirm --clean --onedir `
    --name SistemaPresenca `
    --add-data "img;img" `
    --add-data "ui;ui" `
    --collect-all iconipy `
    --collect-all deepface `
    (Join-Path $PSScriptRoot "app.py")

Write-Host "Executável criado em dist/SistemaPresenca/SistemaPresenca.exe"