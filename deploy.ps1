# ==============================================================================
# CFAO Projets - deploiement (images Docker Hub) avec detection d'hote LAN (Windows)
#   .\deploy.ps1 [-ComposeFile docker-compose.prod.yml] [-EnvFile .env]
# Les valeurs du .env priment ; a defaut, le module est servi en HTTP sur le LAN.
# ==============================================================================
param (
    [string]$ComposeFile = "docker-compose.prod.yml",
    [string]$EnvFile = ".env"
)

if (-not (Test-Path $EnvFile)) { New-Item -ItemType File $EnvFile | Out-Null }

function Get-EnvValue([string]$key) {
    $match = (Get-Content $EnvFile | Where-Object { $_ -match "^$key=(.*)$" } | Select-Object -Last 1)
    if ($match -match "^$key=(.*)$") { return $matches[1].Trim() }
    return $null
}

function Resolve-Value([string]$key, [string]$fallback) {
    $v = [Environment]::GetEnvironmentVariable($key)
    if (-not $v) { $v = Get-EnvValue $key }
    if (-not $v) { $v = $fallback }
    Set-Item "env:$key" $v
    return $v
}

# 1. Secrets : generes une seule fois puis conserves dans le .env (la base
#    est initialisee avec ce mot de passe, il ne doit plus changer).
foreach ($cle in "SECRET_KEY", "POSTGRES_PASSWORD") {
    if (-not (Get-EnvValue $cle)) {
        $octets = New-Object byte[] 48
        [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($octets)
        $valeur = ([Convert]::ToBase64String($octets) -replace '[/+=]', '').Substring(0, 50)
        Add-Content -Path $EnvFile -Value "$cle=$valeur" -Encoding ascii
        Write-Host "[deploy] $cle genere dans $EnvFile" -ForegroundColor Cyan
    }
}

# 2. Hote LAN
$lan = $env:PJ_LAN_HOST
if (-not $lan) { $lan = Get-EnvValue "PJ_LAN_HOST" }
if (-not $lan) {
    try {
        $lan = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Wi-Fi*','Ethernet*' |
                Where-Object { $_.IPAddress -notmatch '^127\.' -and $_.IPAddress -notmatch '^169\.254\.' } |
                Select-Object -First 1).IPAddress
    } catch { }
    if (-not $lan) { $lan = "localhost" }
}

# 3. Port, liaison et URL publique : .env > valeurs LAN
$port = Resolve-Value "PJ_PORT" "8094"
Resolve-Value "PJ_BIND" "0.0.0.0" | Out-Null
$url = Resolve-Value "PJ_PUBLIC_URL" "http://$($lan):$port"
$hote = ($url -replace '^[a-z]+://', '') -replace '[:/].*$', ''
$origines = Resolve-Value "ORIGINES_AUTORISEES" "$url,http://localhost:$port"
Resolve-Value "ALLOWED_HOSTS" "$hote,localhost,127.0.0.1" | Out-Null
$secure = Resolve-Value "COOKIE_SECURE" $(if ($url -like 'https://*') { "True" } else { "False" })

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " CFAO Projets - Deploiement Conteneurs (Windows)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " Fichier Compose  : $ComposeFile"
Write-Host " Fichier d'env    : $EnvFile"
Write-Host " Hote LAN         : $lan" -ForegroundColor Yellow
Write-Host " URL publique     : $url" -ForegroundColor Cyan
Write-Host " Origines         : $origines"
Write-Host " Cookie Secure    : $secure"
Write-Host "==========================================================" -ForegroundColor Green

docker compose --env-file $EnvFile -f $ComposeFile pull
docker compose --env-file $EnvFile -f $ComposeFile up -d
