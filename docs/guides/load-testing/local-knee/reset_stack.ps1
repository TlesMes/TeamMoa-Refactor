<#
측정 전 상태 초기화 (2026-09-11)

왜 필요한가 — 실제로 데인 사례:
  2차(VU 50~1200)를 돌린 뒤 곧바로 VU 400을 재측정했더니 같은 조건인데
  RPS가 286 → 241 (-16%), p95가 1143 → 1792ms (+57%) 로 나왔다.
  원인은 이전 측정에서 누수된 MySQL 커넥션 749개와 그로 인해 불어난
  MySQL 메모리(782MB → 1270MB)였다. 호스트 CPU도 89% → 95%로 올라
  요청당 CPU가 16.8ms → 19.9ms (+18%) 가 됐다.

  즉 **직전 측정의 잔여 상태가 다음 측정을 오염시킨다.**
  앱 프로세스를 재시작하면 앱이 쥔 커넥션이 전부 해제된다(401 → 1 확인).

한계:
  MySQL이 한 번 잡은 메모리는 OS에 거의 반환하지 않는다(1.25 → 1.22GB).
  이건 이 스크립트로 되돌릴 수 없다. 그래서 **모든 실험군에 같은 절차를
  똑같이 적용**해 조건을 맞추는 것이 목적이다. 완전 초기화가 아니다.
  완전 초기화가 필요하면 MySQL까지 재시작해야 하는데, 그러면 버퍼 풀이
  식어서 또 다른 변수가 생긴다. 그 경우 버리는 워밍업 단계를 반드시 넣을 것.

사용:
    powershell -ExecutionPolicy Bypass -File reset_stack.ps1
#>
param(
    [string[]]$WebContainers = @(
        'teammoa_web_lt1', 'teammoa_web_lt2', 'teammoa_web_lt3',
        'teammoa_web_lt4', 'teammoa_web_lt5', 'teammoa_web_lt6'
    )
)

$running = docker ps --filter 'name=teammoa_web_lt' --format '{{.Names}}'
$targets = $WebContainers | Where-Object { $running -contains $_ }

if (-not $targets) { Write-Warning "기동 중인 web 컨테이너가 없다."; exit 1 }

$dbPass = (docker exec teammoa_db_lt printenv MYSQL_ROOT_PASSWORD 2>$null)
if ($dbPass) { $dbPass = $dbPass.Trim() }

function Get-Conn {
    if (-not $dbPass) { return -1 }
    $r = docker exec -e MYSQL_PWD=$dbPass teammoa_db_lt mysql -uroot -N -B `
             -e "SHOW GLOBAL STATUS LIKE 'Threads_connected'" 2>$null
    if ($r) { return [int](($r -split "`t")[1]) }
    return -1
}

Write-Host "초기화 전 MySQL Threads_connected = $(Get-Conn)"
Write-Host "재시작 대상: $($targets -join ', ')"

docker restart @targets | Out-Null

# 전부 health 응답할 때까지 대기 (마이그레이션/collectstatic 완료 확인)
$deadline = (Get-Date).AddMinutes(5)
do {
    Start-Sleep -Seconds 5
    $ok = $true
    foreach ($c in $targets) {
        docker exec $c curl -sf http://localhost:8000/health/ *> $null
        if ($LASTEXITCODE -ne 0) { $ok = $false; break }
    }
} until ($ok -or (Get-Date) -gt $deadline)

if (-not $ok) { Write-Warning "일부 컨테이너가 준비되지 않았다. 상태를 확인할 것."; exit 1 }

Write-Host "초기화 후 MySQL Threads_connected = $(Get-Conn)"
docker stats --no-stream --format '{{.Name}} mem={{.MemUsage}}' teammoa_db_lt
Write-Host "준비 완료. 이제 수집기를 띄우고 측정을 시작할 것."
