#Requires -Version 5.1
<#
.SYNOPSIS
  Start Trace backend (FastAPI) and frontend (Vite) from the project root.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TraceRoot = $PSScriptRoot
$BackendDir = Join-Path $TraceRoot 'backend'
$FrontendDir = Join-Path $TraceRoot 'frontend'
$EnvFile = Join-Path $TraceRoot '.env'
$BackendPort = 8000
$FrontendPort = 5173
$ApiHost = '127.0.0.1'

$script:BackendHost = $null
$script:FrontendHost = $null

function Write-Trace([string]$Message, [ConsoleColor]$Color = [ConsoleColor]::Gray) {
    Write-Host $Message -ForegroundColor $Color
}

function Stop-TraceServers {
    foreach ($name in @('BackendHost', 'FrontendHost')) {
        $proc = Get-Variable -Name $name -Scope Script -ValueOnly -ErrorAction SilentlyContinue
        if ($proc -and -not $proc.HasExited) {
            Write-Trace "Stopping $($proc.ProcessName) (PID $($proc.Id))..." Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

function Test-PortListening([int]$Port) {
    try {
        $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
        if ($listeners) { return $true }
    } catch {
        # Fallback when Get-NetTCPConnection is unavailable
    }
    $pattern = ":$Port\s"
    $line = netstat -ano 2>$null | Select-String -Pattern $pattern
    return $null -ne $line
}

function Get-TracePython {
    $candidates = @(
        (Join-Path $TraceRoot '.venv\Scripts\python.exe'),
        (Join-Path $TraceRoot 'venv\Scripts\python.exe')
    )
    foreach ($path in $candidates) {
        if (Test-Path -LiteralPath $path) { return $path }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Test-EnvConfigured {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        Write-Trace "Missing root .env file. Copy .env.example to .env and set MONGODB_URI." Red
        return $false
    }
    $hasUri = $false
    foreach ($line in Get-Content -LiteralPath $EnvFile -Encoding UTF8) {
        $trim = $line.Trim()
        if ($trim -match '^\s*MONGODB_URI\s*=\s*\S+') { $hasUri = $true; break }
    }
    if (-not $hasUri) {
        Write-Trace ".env exists but MONGODB_URI is missing or empty." Red
        return $false
    }
    return $true
}

function Test-MongoDbConnection([string]$PythonExe) {
    $rootForPy = $TraceRoot -replace '\\', '/'
    $code = @(
        'import sys'
        "from pathlib import Path; root = Path('$rootForPy'); sys.path.insert(0, str(root / 'backend'))"
        'try:'
        '    from app.database.mongodb import ping_database'
        '    sys.exit(0 if ping_database() else 2)'
        'except Exception:'
        '    sys.exit(1)'
    ) -join "`n"

    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $PythonExe -c $code 2>$null
    $exit = $LASTEXITCODE
    $ErrorActionPreference = $prev
    return $exit
}

function Show-MongoDbFailureHelp([int]$ExitCode) {
    Write-Trace '' 
    Write-Trace 'MongoDB connection check FAILED (API will return 503 until this is fixed).' Red
    Write-Trace 'The launcher did not print your connection string or credentials.' Yellow
    Write-Trace '' 
    Write-Trace 'Common causes on Windows + MongoDB Atlas:' Yellow
    Write-Trace '  - TLS/SSL handshake errors (e.g. TLSV1_ALERT_INTERNAL_ERROR): update Windows,' Yellow
    Write-Trace '    ensure system time is correct, try another network, or update Python/certifi/PyMongo.' Yellow
    Write-Trace '  - Atlas IP Access List: add your current public IP (or use Atlas Network Access).' Yellow
    Write-Trace '  - Wrong or expired password in MONGODB_URI (rotate in Atlas, update .env only).' Yellow
    Write-Trace '  - Cluster paused or unreachable; verify status in the Atlas UI.' Yellow
    Write-Trace '' 
    Write-Trace 'Verify manually (no secrets shown): see RUN.md' Yellow
    Write-Trace "  Invoke-RestMethod http://127.0.0.1:$BackendPort/api/health" Gray
    if ($ExitCode -eq 1) {
        Write-Trace '' 
        Write-Trace 'Python could not load the backend or raised an exception during ping.' Yellow
    }
}

function Start-TraceBackend([string]$PythonExe) {
    $backendDirEsc = $BackendDir -replace "'", "''"
    $pythonEsc = $PythonExe -replace "'", "''"
    $cmd = @(
        "Set-Location -LiteralPath '$backendDirEsc'"
        "`$Host.UI.RawUI.WindowTitle = 'Trace Backend ($BackendPort)'"
        "Write-Host 'Trace backend - uvicorn app.main:app' -ForegroundColor Cyan"
        "Write-Host 'Stop: close this window or press Ctrl+C here.' -ForegroundColor DarkGray"
        "& '$pythonEsc' -m uvicorn app.main:app --reload --host $ApiHost --port $BackendPort"
    ) -join '; '
    return Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $cmd
    ) -PassThru -WorkingDirectory $BackendDir
}

function Start-TraceFrontend {
    $frontendDirEsc = $FrontendDir -replace "'", "''"
    $cmd = @(
        "Set-Location -LiteralPath '$frontendDirEsc'"
        "`$Host.UI.RawUI.WindowTitle = 'Trace Frontend ($FrontendPort)'"
        "Write-Host 'Trace frontend - npm run dev' -ForegroundColor Cyan"
        "Write-Host 'Stop: close this window or press Ctrl+C here.' -ForegroundColor DarkGray"
        'npm run dev'
    ) -join '; '
    return Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $cmd
    ) -PassThru -WorkingDirectory $FrontendDir
}

function Wait-BackendHealth {
    param([int]$Seconds = 25)
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $health = Invoke-RestMethod -Uri "http://${ApiHost}:${BackendPort}/api/health" -TimeoutSec 3 -ErrorAction Stop
            if ($health.database -eq 'connected') {
                Write-Trace "Backend health: connected (database: $($health.database_name))." Green
                return $true
            }
            Write-Trace "Backend is up but MongoDB reports: $($health.database)." Yellow
            Show-MongoDbFailureHelp -ExitCode 2
            return $false
        } catch {
            Start-Sleep -Milliseconds 800
        }
    }
    Write-Trace "Backend did not respond on http://${ApiHost}:${BackendPort}/api/health in time." Yellow
    Write-Trace "Check the 'Trace Backend' window for uvicorn errors (missing deps: pip install -r requirements.txt)." Yellow
    return $false
}

# --- Main ---
Set-Location -LiteralPath $TraceRoot
Write-Trace ('Trace launcher - project root: ' + $TraceRoot) Cyan

if (-not (Test-Path -LiteralPath (Join-Path $BackendDir 'app\main.py'))) {
    Write-Trace "Backend not found at $BackendDir\app\main.py" Red
    exit 1
}
if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir 'package.json'))) {
    Write-Trace "Frontend not found at $FrontendDir\package.json" Red
    exit 1
}
if (-not (Test-EnvConfigured)) { exit 1 }

$python = Get-TracePython
if (-not $python) {
    Write-Trace "Python not found. Create .venv and install requirements, or add python to PATH." Red
    exit 1
}
Write-Trace "Using Python: $python" DarkGray

& $python -m uvicorn --help 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Trace "uvicorn is not installed for this Python. Run: pip install -r requirements.txt" Red
    exit 1
}

$node = Get-Command npm -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Trace "npm not found. Install Node.js LTS and run: cd frontend; npm install" Red
    exit 1
}

$nodeModules = Join-Path $FrontendDir 'node_modules'
if (-not (Test-Path -LiteralPath $nodeModules)) {
    Write-Trace "frontend/node_modules missing. Run: cd frontend; npm install" Red
    exit 1
}

if (Test-PortListening -Port $BackendPort) {
    Write-Trace "Port $BackendPort is already in use. Stop the existing backend or change API_PORT in .env." Red
    exit 1
}
if (Test-PortListening -Port $FrontendPort) {
    Write-Trace "Port $FrontendPort is already in use. Stop the existing frontend or change Vite port in vite.config.js." Red
    exit 1
}

Write-Trace "Checking MongoDB (compact mode uses MONGODB_URI from .env)..." DarkGray
$mongoExit = Test-MongoDbConnection -PythonExe $python
if ($mongoExit -eq 0) {
    Write-Trace "MongoDB ping: OK" Green
} else {
    Show-MongoDbFailureHelp -ExitCode $mongoExit
    Write-Trace 'Starting servers anyway - dashboard analytics need a working MongoDB connection.' Yellow
}

Write-Trace "Starting backend on http://${ApiHost}:${BackendPort} ..." Cyan
$script:BackendHost = Start-TraceBackend -PythonExe $python
Start-Sleep -Seconds 2
if ($script:BackendHost.HasExited) {
    Write-Trace "Backend process exited immediately. See errors above or run uvicorn manually from backend/." Red
    exit 1
}

$null = Wait-BackendHealth

Write-Trace "Starting frontend on http://${ApiHost}:${FrontendPort} ..." Cyan
$script:FrontendHost = Start-TraceFrontend
Start-Sleep -Seconds 2
if ($script:FrontendHost.HasExited) {
    Write-Trace "Frontend process exited immediately. Run: cd frontend; npm run dev" Red
    Stop-TraceServers
    exit 1
}

Write-Trace ''
Write-Trace 'Trace is running:' Green
Write-Trace "  Dashboard: http://${ApiHost}:${FrontendPort}" Green
Write-Trace "  API docs:  http://${ApiHost}:${BackendPort}/docs" Green
Write-Trace ''
Write-Trace 'Two log windows opened (Backend / Frontend).' DarkGray
Write-Trace 'Press Ctrl+C in THIS window to stop both servers, or close this window.' Yellow

[Console]::TreatControlCAsInput = $false
try {
    while ($true) {
        if ($script:BackendHost.HasExited) {
            Write-Trace "Backend window closed (exit code $($script:BackendHost.ExitCode))." Yellow
            break
        }
        if ($script:FrontendHost.HasExited) {
            Write-Trace "Frontend window closed (exit code $($script:FrontendHost.ExitCode))." Yellow
            break
        }
        Start-Sleep -Seconds 1
    }
} finally {
    Stop-TraceServers
    Write-Trace 'Trace launcher stopped.' DarkGray
}
