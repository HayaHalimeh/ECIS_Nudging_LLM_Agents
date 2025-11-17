# PowerShell script for Windows
# Set error action preference
$ErrorActionPreference = "Stop"

# -----------------------------
# Logging setup
# -----------------------------
$LOG_DIR = "logs"
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR | Out-Null
}
$LOG_FILE = Join-Path $LOG_DIR "run_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Start-Transcript -Path $LOG_FILE -Append
Write-Host "Logging to $LOG_FILE"

# -----------------------------
# Config 
# -----------------------------
$CASES = @("defaults")
$SETS = @("set_a", "set_b")
$MODEL = "gpt-5"
$REASONING_MODE = @("minimal", "high")

# Starting port for FastAPI servers
$START_PORT = 8000

# -----------------------------
# Seed pool (fixed 200 numbers)
# -----------------------------
$SEED_FILE = "defaults_seeds.txt"

# Read seeds file into an array
$SEEDS = Get-Content $SEED_FILE
$SEED_COUNT = $SEEDS.Count
if ($SEED_COUNT -lt 1) {
    Write-Error "defaults_seeds.txt is empty. Populate it with at least one integer per line."
    exit 1
}

# Initialize seed counter
$SEED_INDEX = 0

# -----------------------------
# Helpers
# -----------------------------
function Get-PortPids {
    param([int]$Port)
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        return $connections.OwningProcess | Select-Object -Unique
    } catch {
        return @()
    }
}

function Wait-ForPortUp {
    param(
        [string]$Host,
        [int]$Port,
        [int]$Timeout = 30
    )
    $elapsed = 0
    while ($elapsed -lt $Timeout) {
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.Connect($Host, $Port)
            $tcpClient.Close()
            return $true
        } catch {
            Start-Sleep -Milliseconds 500
            $elapsed += 0.5
        }
    }
    return $false
}

function Wait-ForPortDown {
    param(
        [int]$Port,
        [int]$Timeout = 30
    )
    $elapsed = 0
    while ($elapsed -lt $Timeout) {
        $pids = Get-PortPids -Port $Port
        if ($pids.Count -eq 0) {
            return $true
        }
        Start-Sleep -Milliseconds 500
        $elapsed += 0.5
    }
    return $false
}

function Stop-ServerOnPort {
    param([int]$Port)
    $pids = Get-PortPids -Port $Port
    if ($pids.Count -eq 0) {
        return
    }
    Write-Host "Stopping processes on port ${Port}: $($pids -join ', ')"
    foreach ($pid in $pids) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "Could not stop process $pid"
        }
    }
    Start-Sleep -Seconds 1
    $remainingPids = Get-PortPids -Port $Port
    if ($remainingPids.Count -gt 0) {
        Write-Host "Forcing kill on port ${Port}..."
        foreach ($pid in $remainingPids) {
            try {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            } catch {}
        }
    }
    if (-not (Wait-ForPortDown -Port $Port -Timeout 10)) {
        Write-Host "Warning: port $Port still busy."
    }
}

# -----------------------------
# Cleanup on exit
# -----------------------------
$cleanup = {
    $pids = Get-PortPids -Port $PORT
    foreach ($pid in $pids) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    Stop-Transcript
}

# Register cleanup
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action $cleanup | Out-Null

# -----------------------------
# Main loop
# -----------------------------
$ROOT_DIR = Get-Location
$PORT = $START_PORT

foreach ($CASE in $CASES) {
    foreach ($SET in $SETS) {
        $APP_DIR = Join-Path $ROOT_DIR "$CASE\$SET"
        $APP_PY = Join-Path $APP_DIR "app.py"

        if (-not (Test-Path $APP_PY)) {
            Write-Host "Skipping ${CASE}/${SET}: app.py not found at $APP_PY"
            continue
        }

        Write-Host "---------------------------------------------"
        Write-Host "Case: $CASE | Set: $SET | Port: $PORT"
        Write-Host "Starting FastAPI dev server..."
        Write-Host "---------------------------------------------"

        # Ensure port is clear
        Stop-ServerOnPort -Port $PORT

        # Run FastAPI dev server in background
        Push-Location $APP_DIR
        $SERVER_JOB = Start-Job -ScriptBlock {
            param($appDir, $port)
            Set-Location $appDir
            uvicorn app:app --host 127.0.0.1 --port $port
        } -ArgumentList $APP_DIR, $PORT
        Pop-Location

        # Give the server a few seconds to boot
        Start-Sleep -Seconds 5

        # Run experiments for each reasoning mode, 50 iterations each
        foreach ($REASONING in $REASONING_MODE) {
            for ($i = 1; $i -le 50; $i++) {
                $SEED = $SEEDS[$SEED_INDEX]
                
                # Check if conversation directory already exists
                $CONV_PATH = Join-Path $APP_DIR "conversations\model-$MODEL-reasoning-$REASONING-seed-$SEED"
                if (Test-Path $CONV_PATH) {
                    Write-Host "Skipping (already exists): ${CASE}/${SET}/conversations/model-$MODEL-reasoning-$REASONING-seed-$SEED"
                    $SEED_INDEX++
                    continue
                }
                
                Write-Host "Running experiment: --case $CASE --set $SET --model $MODEL --reasoning $REASONING --seed $SEED (iteration $i, seed index $SEED_INDEX)"
                Push-Location $ROOT_DIR
                python experiment.py --case $CASE --set $SET --model $MODEL --reasoning $REASONING --seed $SEED
                Pop-Location
                $SEED_INDEX++
            }
        }

        # Stop the FastAPI server for this set
        Write-Host "Shutting down FastAPI server (job $($SERVER_JOB.Id))..."
        Stop-Job -Job $SERVER_JOB
        Remove-Job -Job $SERVER_JOB -Force

    }
}

Stop-Transcript
Write-Host "All done ✅"
