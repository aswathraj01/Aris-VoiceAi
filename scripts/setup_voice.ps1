$ErrorActionPreference = 'Stop'

$root = Join-Path $env:LOCALAPPDATA 'ARIS'
$venv = Join-Path $root 'venv'
$models = Join-Path $root 'models'
$modelName = 'vosk-model-small-en-in-0.4'
$modelPath = Join-Path $models $modelName
$archive = Join-Path $env:TEMP ($modelName + '.zip')
$extractRoot = Join-Path $env:TEMP 'aris-vosk-model-extract'
$python = Get-Command python -ErrorAction SilentlyContinue

if (-not $python) {
    throw 'Python 3.11 or later is required. Install Python, then run this script again.'
}

New-Item -ItemType Directory -Force -Path $root, $models | Out-Null
if (-not (Test-Path (Join-Path $venv 'Scripts\python.exe'))) {
    & $python.Source -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the ARIS voice environment.' }
}
$venvPython = Join-Path $venv 'Scripts\python.exe'
& $venvPython -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot '..\voice\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Could not install the local voice dependencies.' }

if (-not (Test-Path (Join-Path $modelPath 'am'))) {
    if (Test-Path $extractRoot) { Remove-Item -LiteralPath $extractRoot -Recurse -Force }
    Invoke-WebRequest -Uri ('https://alphacephei.com/vosk/models/' + $modelName + '.zip') -OutFile $archive
    Expand-Archive -LiteralPath $archive -DestinationPath $extractRoot -Force
    Move-Item -LiteralPath (Join-Path $extractRoot $modelName) -Destination $modelPath -Force
    Remove-Item -LiteralPath $archive -Force
    Remove-Item -LiteralPath $extractRoot -Recurse -Force
}

Write-Host 'ARIS offline speech recognition is ready.'
Write-Host ('Python: ' + $venvPython)
Write-Host ('Model: ' + $modelPath)
