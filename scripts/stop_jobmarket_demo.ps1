param(
    [switch]$StopPostgres,
    [switch]$StopMonitoring
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PidDir = Join-Path $ProjectRoot "logs\pids"
Set-Location $ProjectRoot

function Stop-ManagedProcess {
    param(
        [string]$Name,
        [string]$PidFile
    )

    if (-not (Test-Path $PidFile)) {
        Write-Host "$Name : aucun processus gere par le script." -ForegroundColor DarkYellow
        return
    }

    $pidValue = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($pidValue) {
        $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
        if ($process) {
            Stop-Process -Id $pidValue -Force
            Write-Host "$Name arrete." -ForegroundColor Green
        }
        else {
            Write-Host "$Name : processus deja arrete." -ForegroundColor DarkYellow
        }
    }

    Remove-Item -Force $PidFile -ErrorAction SilentlyContinue
}

Stop-ManagedProcess -Name "API FastAPI" -PidFile (Join-Path $PidDir "api.pid")
Stop-ManagedProcess -Name "Dashboard Streamlit" -PidFile (Join-Path $PidDir "streamlit.pid")

if ($StopMonitoring) {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if ($docker) {
        & docker compose -f docker-compose.monitoring.yml stop prometheus grafana
    }
    else {
        Write-Warning "Docker n'est pas disponible dans ce terminal."
    }
}

if ($StopPostgres) {
    $serviceNames = @("postgresql-x64-18", "postgresql-x64-17", "postgresql-x64-16")
    foreach ($serviceName in $serviceNames) {
        $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq "Running") {
            Stop-Service -Name $service.Name
            Write-Host "PostgreSQL arrete : $($service.Name)" -ForegroundColor Green
            break
        }
    }
}
