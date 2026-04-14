# Build Installer Script for PPNO
# Strategy: Build a pip wheel, bundle it as an extra file, and install it via post_install.bat

$ErrorActionPreference = "Stop"

# 1. Check for required tools
Write-Host "Checking for required tools..." -ForegroundColor Cyan
if (!(Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Error "Conda not found. Run this from an Anaconda Prompt."
}

# 2. Build a pip wheel from the local source
Write-Host "Building pip wheel..." -ForegroundColor Cyan
$WheelDir = Join-Path (Get-Location) "dist"
if (Test-Path $WheelDir) { Remove-Item -Recurse -Force $WheelDir }
New-Item -ItemType Directory -Path $WheelDir

pip wheel . --no-deps -w $WheelDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip wheel failed with exit code $LASTEXITCODE"
}

# Find the generated wheel file
$WheelFile = Get-ChildItem -Path $WheelDir -Filter "*.whl" | Select-Object -First 1
if (-not $WheelFile) {
    Write-Error "No .whl file found in $WheelDir"
}
Write-Host "Wheel built: $($WheelFile.Name)" -ForegroundColor Green

# Extract version from wheel name
$WheelVersion = $WheelFile.BaseName -replace '^ppno-([\d.]+)-.*', '$1'

# 3. Prepare the construct_temp.yaml
Write-Host "Preparing constructor configuration..." -ForegroundColor Cyan
$TempConstruct = "construct_temp.yaml"

# Paths must use forward slashes in YAML
$WheelPathYaml = ($WheelFile.FullName -replace "\\", "/")
$PostInstallPathYaml = ((Join-Path (Get-Location) "post_install.bat") -replace "\\", "/")

# Pre-build YAML lines that would confuse PowerShell's here-string parser
$ExtraFileLine = "  - ${WheelPathYaml}: pkgs_pip/$($WheelFile.Name)"

$ConstructContent = @"
name: PPNO
version: $WheelVersion
company: Andres Garcia Martinez

channels:
  - conda-forge
  - defaults

specs:
  - python=3.9.*
  - numpy
  - scipy
  - pygmo

extra_files:
$ExtraFileLine

post_install: $PostInstallPathYaml
"@

# Save without BOM
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText(
    (Join-Path (Get-Location) $TempConstruct),
    $ConstructContent,
    $Utf8NoBom
)

# 4. Run Constructor
Write-Host "Running Constructor to generate the installer..." -ForegroundColor Cyan
constructor . --config $TempConstruct

if ($LASTEXITCODE -ne 0) {
    Write-Error "Constructor failed with exit code $LASTEXITCODE"
}

# 5. Summary
if (Get-ChildItem -Path . -Filter "*.exe" -ErrorAction SilentlyContinue) {
    Write-Host "`nDone! Look for a .exe file in the current directory." -ForegroundColor Green
} else {
    Write-Error "Executable not found! Constructor may have failed silently."
}
