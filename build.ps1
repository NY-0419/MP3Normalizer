$ErrorActionPreference = "Stop"

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    throw "PyInstaller was not found. Run: python -m pip install -r requirements.txt"
}

if (-not (Test-Path 'ffmpeg\bin\ffmpeg.exe')) {
    throw 'ffmpeg\bin\ffmpeg.exe was not found.'
}

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$buildConfig = (& 'ffmpeg\bin\ffmpeg.exe' -buildconf 2>&1 | Out-String)
$ErrorActionPreference = $previousErrorActionPreference
if ($buildConfig -match '--enable-gpl' -or $buildConfig -match '--enable-nonfree') {
    throw 'The bundled FFmpeg is GPL or nonfree. Replace it with an LGPL-compatible build.'
}
if ($buildConfig -notmatch '--enable-shared' -or $buildConfig -match '--enable-static') {
    throw 'The bundled FFmpeg must be a shared-library build for LGPL distribution.'
}
foreach ($forbidden in @('--enable-libx264', '--enable-libx265', '--enable-libxvid', '--enable-libfdk_aac')) {
    if ($buildConfig -match [regex]::Escape($forbidden)) {
        throw "The bundled FFmpeg uses a forbidden GPL/nonfree component: $forbidden"
    }
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
