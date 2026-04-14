# Build Installer Script for PPNO
# This script automates the creation of a standalone .exe installer using Constructor.

$ErrorActionPreference = "Stop"

# 1. Check for required tools
Write-Host "Checking for required tools..." -ForegroundColor Cyan
if (!(Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Error "Conda not found. Please install Miniconda or Anaconda."
}

# Install conda-build and constructor if missing
Write-Host "Ensuring conda-build and constructor are installed..." -ForegroundColor Cyan
conda install -y conda-build constructor -c conda-forge

# 2. Build the PPNO conda package
Write-Host "Building PPNO conda package..." -ForegroundColor Cyan
$BuildDir = Join-Path (Get-Location) "conda-out"
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
New-Item -ItemType Directory -Path $BuildDir

# Run conda-build
conda build conda.recipe --output-folder $BuildDir --no-anaconda-upload -c conda-forge

# 3. Create a temporary construct.yaml with the local channel
Write-Host "Preparing constructor configuration..." -ForegroundColor Cyan
$LocalChannel = "file:///" + ($BuildDir -replace "\\", "/")
$OriginalConstruct = Get-Content construct.yaml -Raw
$TempConstruct = "construct_temp.yaml"

# Insert the local channel at the beginning of the channels list
$UpdatedConstruct = $OriginalConstruct -replace "channels:", "channels:`n  - $LocalChannel"
$UpdatedConstruct | Out-File $TempConstruct -Encoding utf8

# 4. Run Constructor
Write-Host "Running Constructor to generate the installer..." -ForegroundColor Cyan
constructor . --config $TempConstruct

# 5. Cleanup
Write-Host "Cleaning up temporary files..." -ForegroundColor Cyan
# Remove-Item $TempConstruct

Write-Host "`nDone! Look for a .exe file in the current directory." -ForegroundColor Green
