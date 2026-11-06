$ErrorActionPreference = "Stop"

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    throw "PyInstaller was not found. Run: python -m pip install -r requirements.txt"
}

if (-not (Test-Path 'ffmpeg\bin\ffmpeg.exe')) {
    throw 'ffmpeg\bin\ffmpeg.exe was not found.'
}

if (-not (Test-Path 'image.ico')) {
    throw 'image.ico was not found.'
}

if (-not (Test-Path 'readme.txt')) {
    throw 'readme.txt was not found.'
}

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
pyinstaller --noconfirm --clean mp3_normalizer.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE"
}
Copy-Item -LiteralPath 'readme.txt' -Destination 'dist\MP3Normalizer\readme.txt' -Force
Write-Host "Build complete: dist\MP3Normalizer\MP3Normalizer.exe"
