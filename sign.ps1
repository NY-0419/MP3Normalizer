param(
    [Parameter(Mandatory = $true)]
    [string]$CertificateThumbprint,
    [string]$SignToolPath = "signtool.exe",
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"
$target = Join-Path $PSScriptRoot "dist\MP3Normalizer\MP3Normalizer.exe"

if (-not (Test-Path $target)) {
    throw "Build output was not found: $target"
}

if (-not (Get-Command $SignToolPath -ErrorAction SilentlyContinue)) {
    throw "signtool.exe was not found. Install the Windows SDK or pass -SignToolPath."
}

$thumbprint = $CertificateThumbprint.Replace(" ", "").ToUpperInvariant()
$certificate = Get-ChildItem "Cert:\CurrentUser\My\$thumbprint" -ErrorAction SilentlyContinue
if (-not $certificate) {
    throw "Signing certificate was not found in the current user's certificate store."
}
if (-not $certificate.HasPrivateKey) {
    throw "The signing certificate does not have a private key."
}

& $SignToolPath sign /sha1 $thumbprint /fd SHA256 /tr $TimestampUrl /td SHA256 $target
if ($LASTEXITCODE -ne 0) {
    throw "Signing failed with exit code $LASTEXITCODE"
}

& $SignToolPath verify /pa $target
if ($LASTEXITCODE -ne 0) {
    throw "Signature verification failed with exit code $LASTEXITCODE"
}

Write-Host "Signature verified: $target"
