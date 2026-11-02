param(
    [Parameter(Mandatory=$true)]
    [ValidateNotNullOrEmpty()]
    [string]$ApiBase,
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$base = $ApiBase.TrimEnd('/')
$uri = $null
if (![uri]::TryCreate($base, [UriKind]::Absolute, [ref]$uri) -or
    $uri.Scheme -ne 'https' -or
    $uri.Host -in @('maydrinks.surge.sh', 'localhost', '127.0.0.1') -or
    $uri.AbsolutePath -ne '/api' -or
    $uri.Query -or $uri.Fragment -or $uri.UserInfo -or $uri.Port -ne 443) {
    throw 'ApiBase must be a public HTTPS URL ending in /api (not Surge or localhost).'
}

Write-Host "Checking public API: $base/health"
try {
    $health = Invoke-WebRequest -Uri "$base/health" -UseBasicParsing -TimeoutSec 120
    if ([string]$health.Headers['Content-Type'] -notmatch 'application/json') { throw 'Health is not JSON.' }
    $result = $health.Content | ConvertFrom-Json
    if ($result.status -ne 'ok' -or $result.database -ne 'SQL Server') { throw 'SQL Server health check failed.' }

    $catalog = Invoke-WebRequest -Uri "$base/catalog" -Headers @{'Origin'='https://maydrinks.surge.sh'} -UseBasicParsing -TimeoutSec 120
    if ([string]$catalog.Headers['Content-Type'] -notmatch 'application/json') { throw 'Catalog is not JSON.' }
    if ($catalog.Headers['Access-Control-Allow-Origin'] -ne 'https://maydrinks.surge.sh') { throw 'Catalog CORS is not configured for Surge.' }
    $items = $catalog.Content | ConvertFrom-Json
    if (!$items.drinks -or $items.drinks.Count -lt 1) { throw 'Catalog has no active drinks. Seed the cloud database before deploying.' }

    $preflight = Invoke-WebRequest -Method OPTIONS -Uri "$base/auth/login" -Headers @{'Origin'='https://maydrinks.surge.sh';'Access-Control-Request-Method'='POST';'Access-Control-Request-Headers'='content-type'} -UseBasicParsing -TimeoutSec 120
    if ($preflight.Headers['Access-Control-Allow-Origin'] -ne 'https://maydrinks.surge.sh' -or
        [string]$preflight.Headers['Access-Control-Allow-Methods'] -notmatch 'POST' -or
        [string]$preflight.Headers['Access-Control-Allow-Headers'] -notmatch 'content-type') {
        throw 'Login CORS preflight is not configured for Surge.'
    }
} catch { throw "Deployment stopped: $($_.Exception.Message)" }
Write-Host 'SQL Server, catalog and CORS checks passed.' -ForegroundColor Green
if ($VerifyOnly) { return }
if (!(Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'npm is not installed.' }
if (!(Get-Command surge.cmd -ErrorAction SilentlyContinue)) { throw 'Surge CLI is not installed or signed in.' }
$previousApiUrl = [Environment]::GetEnvironmentVariable('VITE_API_URL', 'Process')
$env:VITE_API_URL = $base
Push-Location $project
try {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    Copy-Item (Join-Path $project 'dist/index.html') (Join-Path $project 'dist/200.html') -Force
    & surge.cmd (Join-Path $project 'dist') maydrinks.surge.sh
    if ($LASTEXITCODE -ne 0) { throw 'Surge deployment failed.' }
    Write-Host 'Frontend deployed with verified public HTTPS API.' -ForegroundColor Green
} finally {
    Pop-Location
    [Environment]::SetEnvironmentVariable('VITE_API_URL', $previousApiUrl, 'Process')
}
