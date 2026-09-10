<#
서버 PC 자원 사용량 수집기 (부하 테스트 단계마다 실행)

"서버가 한계였다"를 증명하려면 부하 곡선만으로는 부족하다. 같은 시간대의
CPU / 메모리 / DB 커넥션이 함께 있어야 무엇이 먼저 닿았는지 말할 수 있다.

사용법 (단계 시작 직전에 띄우고, 단계 끝나면 Ctrl+C):
    powershell -ExecutionPolicy Bypass -File monitor_server.ps1 -Stage vu050 -DurationSec 200
#>
param(
    [Parameter(Mandatory = $true)][string]$Stage,
    [int]$DurationSec = 200,
    [int]$IntervalSec = 3,
    [string]$OutDir
)

# $PSScriptRoot 는 호출 방식에 따라 비어 있을 수 있다. 비면 출력이 드라이브
# 루트로 새어나가 결과를 잃는다. 여러 경로로 스크립트 위치를 복원한다.
if (-not $OutDir) {
    $root = $PSScriptRoot
    if (-not $root) { $root = Split-Path -Parent $MyInvocation.MyCommand.Path }
    if (-not $root) { $root = (Get-Location).Path }
    $OutDir = Join-Path $root "results"
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Write-Host "출력 디렉터리: $OutDir"
$out = Join-Path $OutDir "server_$Stage.csv"

# MySQL 접속 정보는 컨테이너 환경변수에서 직접 읽는다.
# 호스트 셸의 $env:DB_ROOT_PASSWORD 에 의존하면 값이 없을 때 조용히
# 기본값으로 떨어져 커넥션 수가 전 구간 -1로 기록된다 (실제로 그랬다).
# DB가 먼저 한계에 닿았는지 판정하는 핵심 지표라 실패를 드러내야 한다.
$dbPass = (docker exec teammoa_db_lt printenv MYSQL_ROOT_PASSWORD 2>$null)
if ($dbPass) { $dbPass = $dbPass.Trim() }
if (-not $dbPass) {
    Write-Warning "MySQL 루트 패스워드를 얻지 못했다. 커넥션 수가 -1로 기록된다."
} else {
    $probe = docker exec -e MYSQL_PWD=$dbPass teammoa_db_lt mysql -uroot -N -B -e "SHOW GLOBAL STATUS LIKE 'Threads_connected'" 2>$null
    if ($probe) { Write-Host "MySQL 지표 수집 확인: $probe" }
    else { Write-Warning "MySQL 조회 실패. 커넥션 수가 -1로 기록된다." }
}

"ts,host_cpu_pct,web_cpu_pct,web_mem_mb,db_cpu_pct,db_mem_mb,redis_cpu_pct,mysql_threads_connected,mysql_threads_running,web_count,nginx_cpu_pct" |
    Out-File -FilePath $out -Encoding utf8

Write-Host "수집 시작 -> $out  ($DurationSec 초, $IntervalSec 초 간격)"
$deadline = (Get-Date).AddSeconds($DurationSec)

while ((Get-Date) -lt $deadline) {
    $ts = (Get-Date).ToString("o")

    # 호스트 전체 CPU
    try {
        $hostCpu = [math]::Round(
            (Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction Stop).CounterSamples[0].CookedValue, 1)
    } catch { $hostCpu = -1 }

    # 컨테이너별 CPU / 메모리
    # web 컨테이너는 1개(단일 프로세스)일 수도, teammoa_web_lt1..N(멀티프로세스)
    # 일 수도 있다. 이름으로 전부 찾아 **합산**한다. 합산하지 않으면 멀티프로세스
    # 구성에서 프로세스 하나의 CPU만 보고 "아직 여유 있다"고 오독하게 된다.
    $web = @{cpu = -1; mem = -1}; $db = @{cpu = -1; mem = -1}; $redisCpu = -1
    $webCount = 0
    $nginxCpu = -1
    try {
        $raw = docker stats --no-stream --format "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}" 2>$null
        $webCpu = 0.0; $webMem = 0.0
        foreach ($line in $raw) {
            $p = $line -split '\|'
            if ($p.Count -lt 3) { continue }
            $name = $p[0]
            $cpu = [double]($p[1] -replace '%', '')
            $memRaw = ($p[2] -split '/')[0].Trim()
            $mem = [double]($memRaw -replace '[A-Za-z]', '')
            if ($memRaw -match 'GiB') { $mem = $mem * 1024 }
            if ($memRaw -match 'KiB') { $mem = $mem / 1024 }
            if ($name -like 'teammoa_web_lt*') {
                $webCpu += $cpu; $webMem += $mem; $webCount++
            }
            elseif ($name -eq 'teammoa_db_lt')    { $db = @{cpu = $cpu; mem = [math]::Round($mem, 1)} }
            elseif ($name -eq 'teammoa_redis_lt') { $redisCpu = $cpu }
            elseif ($name -eq 'teammoa_nginx_lt') { $nginxCpu = $cpu }
        }
        if ($webCount -gt 0) {
            $web = @{cpu = [math]::Round($webCpu, 2); mem = [math]::Round($webMem, 1)}
        }
    } catch { }

    # MySQL 커넥션 수 — DB가 먼저 한계에 닿았는지 판정하는 핵심 지표
    $connected = -1; $running = -1
    try {
        $status = docker exec -e MYSQL_PWD=$dbPass teammoa_db_lt mysql -uroot -N -B `
                      -e "SHOW GLOBAL STATUS LIKE 'Threads%'" 2>$null
        foreach ($line in $status) {
            $p = $line -split "`t"
            if ($p[0] -eq 'Threads_connected') { $connected = [int]$p[1] }
            if ($p[0] -eq 'Threads_running')   { $running = [int]$p[1] }
        }
    } catch { }

    "$ts,$hostCpu,$($web.cpu),$($web.mem),$($db.cpu),$($db.mem),$redisCpu,$connected,$running,$webCount,$nginxCpu" |
        Out-File -FilePath $out -Encoding utf8 -Append

    Start-Sleep -Seconds $IntervalSec
}

Write-Host "수집 완료 -> $out"
