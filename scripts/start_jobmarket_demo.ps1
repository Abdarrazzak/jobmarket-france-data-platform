param(
    [switch]$SkipPostgres,
    [switch]$SkipMonitoring,
    [switch]$RestartMonitoring
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LogDir = Join-Path $ProjectRoot "logs"
$PidDir = Join-Path $LogDir "pids"
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
Set-Location $ProjectRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-Http {
    param([string]$Url)
    try {
        Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Wait-Http {
    param(
        [string]$Name,
        [string]$Url,
        [int]$Retries = 20
    )

    for ($i = 1; $i -le $Retries; $i++) {
        if (Test-Http -Url $Url) {
            Write-Host "$Name est disponible : $Url" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 1
    }

    Write-Warning "$Name n'a pas repondu apres $Retries secondes. Consulte les logs dans $LogDir."
    return $false
}

function Start-Postgres {
    Write-Step "Demarrage de PostgreSQL"

    $serviceNames = @("postgresql-x64-18", "postgresql-x64-17", "postgresql-x64-16")
    $service = $null

    foreach ($serviceName in $serviceNames) {
        $candidate = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($candidate) {
            $service = $candidate
            break
        }
    }

    if (-not $service) {
        Write-Warning "Aucun service PostgreSQL 16/17/18 detecte. Lance PostgreSQL manuellement si l'API ne repond pas."
        return
    }

    if ($service.Status -ne "Running") {
        Start-Service -Name $service.Name
        $service.WaitForStatus("Running", "00:00:20")
    }

    Write-Host "PostgreSQL est lance : $($service.Name)" -ForegroundColor Green
}

function Start-PythonService {
    param(
        [string]$Name,
        [string[]]$Arguments,
        [string]$HealthUrl,
        [string]$PidFile,
        [string]$StdoutFile,
        [string]$StderrFile
    )

    Write-Step "Demarrage de $Name"

    if (Test-Http -Url $HealthUrl) {
        Write-Host "$Name est deja disponible : $HealthUrl" -ForegroundColor Green
        return
    }

    if (-not (Test-Path $PythonPath)) {
        throw "Python introuvable dans .venv. Lance d'abord : python -m venv .venv puis pip install -e `".[all,dev,windows]`""
    }

    if (Test-Path $PidFile) {
        $oldPid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($oldPid) {
            $oldProcess = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
            if ($oldProcess) {
                Stop-Process -Id $oldPid -Force
                Start-Sleep -Seconds 1
            }
        }
        Remove-Item -Force $PidFile -ErrorAction SilentlyContinue
    }

    $process = Start-Process `
        -FilePath $PythonPath `
        -ArgumentList $Arguments `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardOutput $StdoutFile `
        -RedirectStandardError $StderrFile `
        -WindowStyle Hidden `
        -PassThru

    Set-Content -Path $PidFile -Value $process.Id
    Wait-Http -Name $Name -Url $HealthUrl | Out-Null
}

function Start-Monitoring {
    Write-Step "Demarrage Prometheus et Grafana"

    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        Write-Warning "Docker n'est pas disponible dans ce terminal. Monitoring ignore."
        return
    }

    if ($RestartMonitoring) {
        & docker compose -f docker-compose.monitoring.yml restart prometheus grafana
    }
    else {
        & docker compose -f docker-compose.monitoring.yml up -d prometheus grafana
    }

    Wait-Http -Name "Prometheus" -Url "http://localhost:9090/-/ready" -Retries 30 | Out-Null
    Wait-Http -Name "Grafana" -Url "http://localhost:3000/login" -Retries 30 | Out-Null
}

if (-not $SkipPostgres) {
    Start-Postgres
}

Start-PythonService `
    -Name "API FastAPI" `
    -Arguments @("-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000") `
    -HealthUrl "http://127.0.0.1:8000/health" `
    -PidFile (Join-Path $PidDir "api.pid") `
    -StdoutFile (Join-Path $LogDir "api.out.log") `
    -StderrFile (Join-Path $LogDir "api.err.log")

Start-PythonService `
    -Name "Dashboard Streamlit" `
    -Arguments @("-m", "streamlit", "run", "dashboard\app.py", "--server.address", "127.0.0.1", "--server.port", "8501", "--server.headless", "true", "--browser.gatherUsageStats", "false") `
    -HealthUrl "http://127.0.0.1:8501" `
    -PidFile (Join-Path $PidDir "streamlit.pid") `
    -StdoutFile (Join-Path $LogDir "streamlit.out.log") `
    -StderrFile (Join-Path $LogDir "streamlit.err.log")

if (-not $SkipMonitoring) {
    Start-Monitoring
}

Write-Host ""
Write-Host "Demo JobMarket prete." -ForegroundColor Green
Write-Host "API Swagger : http://127.0.0.1:8000/docs"
Write-Host "Dashboard   : http://127.0.0.1:8501"
Write-Host "Prometheus  : http://localhost:9090"
Write-Host "Grafana     : http://localhost:3000"
Write-Host "Logs        : $LogDir"
