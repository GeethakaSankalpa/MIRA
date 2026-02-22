$ErrorActionPreference = "Stop"

# Helper function for colored status output
function Write-Status {
    param($Name, $Status, $Ports, $Health, $Uptime)
    
    $statusColor = if ($Status -eq "running") { "Green" } 
                   elseif ($Status -eq "exited") { "Red" } 
                   else { "Yellow" }
    
    $healthColor = if ($Health -eq "healthy") { "Green" }
                   elseif ($Health -eq "unhealthy") { "Red" }
                   elseif ($Health -eq "starting") { "Yellow" }
                   else { "Gray" }

    Write-Host "  $Name" -ForegroundColor Cyan -NoNewline
    Write-Host " [$Status]" -ForegroundColor $statusColor -NoNewline

    if ($Health -and $Health -ne "N/A") {
        Write-Host " (Health: $Health)" -ForegroundColor $healthColor -NoNewline
    }

    Write-Host " | Up: $Uptime"

    if ($Ports) {
        $portList = $Ports -split ", "
        foreach ($port in $portList) {
            Write-Host "       Port: $port" -ForegroundColor DarkCyan
        }
    } else {
        Write-Host "       Port: (none exposed)" -ForegroundColor DarkGray
    }
}

# ── Header ──────────────────────────────────────────────────────────
Clear-Host
Write-Host ""
Write-Host "+======================================================+" -ForegroundColor Magenta
Write-Host "|         MIRA Dev Environment Status                  |" -ForegroundColor Magenta
Write-Host "+======================================================+" -ForegroundColor Magenta
Write-Host "  Checked at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# ── Docker Compose Raw Status ────────────────────────────────────────
Write-Host "-- Docker Compose Overview -----------------------------" -ForegroundColor Yellow
Set-Location "E:\MIRA\infra"
docker compose ps
Write-Host ""

# ── Per-Container Detailed Status ───────────────────────────────────
Write-Host "-- Container Details -----------------------------------" -ForegroundColor Yellow

$dockerFormat = '{{.Names}}|{{.Status}}|{{.Ports}}|{{.RunningFor}}'
$containers = docker ps -a --filter "name=mira-" --format $dockerFormat 2>$null

if (-not $containers) {
    Write-Host "  No MIRA containers found." -ForegroundColor Red
} else {
    foreach ($line in $containers) {
        $parts     = $line -split '\|'
        $name      = $parts[0]
        $rawStatus = $parts[1]
        $ports     = $parts[2]
        $uptime    = $parts[3]

        $state = if ($rawStatus -match '^Up') { "running" }
                 elseif ($rawStatus -match '^Exited') { "exited" }
                 elseif ($rawStatus -match '^Restarting') { "restarting" }
                 else { $rawStatus }

        $health = if ($rawStatus -match '\((\w+)\)') { $Matches[1] } else { "N/A" }

        Write-Status -Name $name -Status $state -Ports $ports -Health $health -Uptime $uptime
        Write-Host ""
    }
}

# ── Summary ──────────────────────────────────────────────────────────
Write-Host "-- Summary ---------------------------------------------" -ForegroundColor Yellow

$allNames     = docker ps -a --filter "name=mira-" --format '{{.Names}}' 2>$null
$runningNames = docker ps    --filter "name=mira-" --format '{{.Names}}' 2>$null

$totalCount   = if ($allNames)     { @($allNames).Count }     else { 0 }
$runningCount = if ($runningNames) { @($runningNames).Count } else { 0 }
$stoppedCount = $totalCount - $runningCount

Write-Host "  Total   : $totalCount"   -ForegroundColor White
Write-Host "  Running : $runningCount" -ForegroundColor Green
Write-Host "  Stopped : $stoppedCount" -ForegroundColor $(if ($stoppedCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

# ── Quick Port Map ───────────────────────────────────────────────────
Write-Host "-- Port Map (running containers only) ------------------" -ForegroundColor Yellow

$portFormat = '{{.Names}}|{{.Status}}|{{.Ports}}'
$portLines  = docker ps --filter "name=mira-" --format $portFormat 2>$null

if ($portLines) {
    Write-Host ("  {0,-35} {1,-25} {2}" -f "NAME", "STATUS", "PORTS") -ForegroundColor Gray
    Write-Host ("  {0,-35} {1,-25} {2}" -f "----", "------", "-----") -ForegroundColor DarkGray
    foreach ($pl in $portLines) {
        $pp = $pl -split '\|'
        Write-Host ("  {0,-35} {1,-25} {2}" -f $pp[0], $pp[1], $pp[2]) -ForegroundColor White
    }
} else {
    Write-Host "  No running containers." -ForegroundColor DarkGray
}
Write-Host ""

# ── Alerts ───────────────────────────────────────────────────────────
Write-Host "-- Alerts ----------------------------------------------" -ForegroundColor Yellow

$unhealthy        = docker ps -a --filter "name=mira-" --filter "health=unhealthy" --format '{{.Names}}' 2>$null
$exitedContainers = docker ps -a --filter "name=mira-" --filter "status=exited"    --format '{{.Names}}' 2>$null

if ($unhealthy) {
    Write-Host "  [!] UNHEALTHY containers detected:" -ForegroundColor Red
    foreach ($c in $unhealthy) {
        Write-Host "      - $c" -ForegroundColor Red
    }
    Write-Host ""
}

if ($exitedContainers) {
    Write-Host "  [!] STOPPED containers detected:" -ForegroundColor Red
    foreach ($c in $exitedContainers) {
        Write-Host "      - $c" -ForegroundColor Red
    }
    Write-Host ""
}

if (-not $unhealthy -and -not $exitedContainers) {
    Write-Host "  [OK] All MIRA containers are UP and HEALTHY" -ForegroundColor Green
    Write-Host ""
}

Write-Host "+======================================================+" -ForegroundColor Magenta
Write-Host "|                   End of Report                      |" -ForegroundColor Magenta
Write-Host "+======================================================+" -ForegroundColor Magenta