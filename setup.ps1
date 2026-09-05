$ErrorActionPreference = "Stop"

Write-Host "Setting up JobAgent..." -ForegroundColor Cyan

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"

Write-Host "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Installing Playwright Chromium..."
python -m playwright install chromium

Write-Host ""
Write-Host "JobAgent setup complete." -ForegroundColor Green
Write-Host "Activate the environment with:"
Write-Host ".\.venv\Scripts\Activate.ps1"