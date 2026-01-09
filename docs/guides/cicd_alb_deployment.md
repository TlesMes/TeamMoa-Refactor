# CI/CD with ALB Rolling Update Deployment Guide

> **TeamMoa ALB 환경에서 무중단 배포를 위한 CI/CD 파이프라인 가이드**
>
> GitHub Actions를 사용한 Rolling Update 전략으로 Web1, Web2를 순차적으로 배포합니다.

---

## 📋 목차

1. [개요](#개요)
2. [Rolling Update 전략](#rolling-update-전략)
3. [GitHub Secrets 설정](#github-secrets-설정)
4. [배포 프로세스](#배포-프로세스)
5. [Health Check 설정](#health-check-설정)
6. [트러블슈팅](#트러블슈팅)
7. [배포 모니터링](#배포-모니터링)

---

## 개요

### 🎯 목표
- **완전 무중단 배포**: 사용자가 서비스 중단을 경험하지 않음
- **자동화된 롤백**: Health Check 실패 시 배포 자동 중단
- **순차 배포**: Web1 → Health Check → Web2 순서로 안전하게 배포

### 🏗️ 아키텍처

```
GitHub Actions (CI/CD Runner)
    ↓ (Test → Build → Deploy)
Docker Hub (이미지 저장소)
    ↓
┌─────────────────────────────────────────┐
│  AWS Application Load Balancer (ALB)   │
│  Target Group: teammoa-tg               │
└─────────────────────────────────────────┘
    ↓                           ↓
┌──────────────┐          ┌──────────────┐
│  EC2-Web1    │          │  EC2-Web2    │
│  (2a)        │          │  (2b)        │
│  Nginx:80    │          │  Nginx:80    │
│  Django:8000 │          │  Django:8000 │
└──────────────┘          └──────────────┘
```

### 🔄 배포 흐름

```
1. git push origin main
   ↓
2. GitHub Actions Trigger
   ↓
<!-- AUTO:TEST_COUNT -->
3. Test (pytest 264개 테스트)
   ↓
4. Update Documentation (테스트 통계 자동 업데이트)
   ↓
5. Build (Docker 이미지 빌드 + Docker Hub 푸시)
   ↓
6. Deploy (Rolling Update)
   ├─ Web1 Deregister → Deploy → Health Check → Register
   └─ Web2 Deregister → Deploy → Health Check → Register
   ↓
7. Verify (최종 확인)
   ↓
8. Complete ✅
```

---

## Rolling Update 전략

### 📊 배포 단계별 트래픽 분산

```
초기 상태:
ALB → Web1 (50%) + Web2 (50%)
사용자: 정상 접속 ✅

Step 1: Web1 배포 시작
ALB → Web2 (100%)              ← Web1 Deregister
사용자: 정상 접속 ✅ (Web2만 사용)

Step 2: Web1 배포 완료
ALB → Web1 (50%) + Web2 (50%)  ← Web1 Register
사용자: 정상 접속 ✅

Step 3: Web2 배포 시작
ALB → Web1 (100%)              ← Web2 Deregister
사용자: 정상 접속 ✅ (Web1만 사용)

Step 4: Web2 배포 완료
ALB → Web1 (50%) + Web2 (50%)  ← Web2 Register
사용자: 정상 접속 ✅

✅ 전 과정에서 다운타임 0초!
```

### ⏱️ 배포 소요 시간

<!-- AUTO:TEST_COUNT -->
| 단계 | 소요 시간 | 설명 |
|-----|---------|-----|
| Test | 2~3분 | pytest 249개 테스트 실행 |
| Update Docs | ~10초 | 테스트 통계 자동 업데이트 (변경 시 커밋) |
| Build | 3~5분 | Docker 이미지 빌드 + 푸시 |
| **Deploy Web1** | **3분** | Deregister(30s) + Deploy(1m) + Health Check(90s) |
| **Deploy Web2** | **3분** | Deregister(30s) + Deploy(1m) + Health Check(90s) |
| **총 소요 시간** | **11~14분** | git push부터 배포 완료까지 |

---

## GitHub Secrets 설정

### 필수 Secrets 목록

**AWS Credentials:**
```
AWS_ACCESS_KEY_ID          # AWS IAM 사용자 Access Key
AWS_SECRET_ACCESS_KEY      # AWS IAM 사용자 Secret Key
```

**EC2 인스턴스 정보:**
```
EC2_WEB1_ID                # Web1 인스턴스 ID (예: i-081d1db7ba79277b1)
EC2_WEB1_HOST              # Web1 Public IP 또는 Private IP
EC2_WEB2_ID                # Web2 인스턴스 ID (예: i-0b914c0dec41ec170)
EC2_WEB2_HOST              # Web2 Public IP 또는 Private IP
EC2_USERNAME               # EC2 SSH 사용자명 (예: ubuntu)
EC2_SSH_KEY                # EC2 SSH Private Key (PEM 형식)
```

**AWS 리소스:**
```
TARGET_GROUP_ARN           # ALB Target Group ARN
WEB_SECURITY_GROUP_ID      # Web 서버 Security Group ID (SSH 허용용)
```

**Docker Hub:**
```
DOCKER_USERNAME            # Docker Hub 사용자명
DOCKER_PASSWORD            # Docker Hub 비밀번호
```

### GitHub Secrets 등록 방법

1. **GitHub 저장소 접속**
   - `https://github.com/TlesMes/TeamMoa-Refactor`

2. **Settings → Secrets and variables → Actions**
   - `New repository secret` 클릭

3. **각 Secret 등록**
   ```
   Name: EC2_WEB1_ID
   Value: i-081d1db7ba79277b1
   ```

### 💡 값 확인 방법

**EC2 인스턴스 ID 확인:**
```bash
# AWS Console
EC2 → Instances → Web1/Web2 선택 → Instance ID 복사

# 또는 AWS CLI
aws ec2 describe-instances \
    --region ap-northeast-2 \
    --query "Reservations[].Instances[].[InstanceId,Tags[?Key=='Name'].Value|[0]]" \
    --output table
```

**Target Group ARN 확인:**
```bash
# AWS Console
EC2 → Load Balancing → Target Groups → teammoa-tg 선택 → ARN 복사

# 또는 AWS CLI
aws elbv2 describe-target-groups \
    --region ap-northeast-2 \
    --query "TargetGroups[?TargetGroupName=='teammoa-tg'].TargetGroupArn" \
    --output text
```

**Security Group ID 확인:**
```bash
# AWS Console
EC2 → Security Groups → Web 서버용 SG 선택 → Group ID 복사

# 또는 AWS CLI
aws ec2 describe-security-groups \
    --region ap-northeast-2 \
    --filters "Name=group-name,Values=*web*" \
    --query "SecurityGroups[].GroupId" \
    --output text
```

**SSH Key 확인:**
```bash
# PEM 파일 전체 내용을 복사 (개행 포함)
cat ~/.ssh/teammoa-key.pem

# 또는 클립보드에 복사 (Windows)
cat ~/.ssh/teammoa-key.pem | clip

# 또는 클립보드에 복사 (Mac)
cat ~/.ssh/teammoa-key.pem | pbcopy
```

---

## 배포 프로세스

### 1. 코드 커밋 및 푸시

```bash
# 로컬에서 코드 수정
git add .
git commit -m "feat(api): 새 기능 추가"
git push origin main
```

### 2. GitHub Actions 자동 실행

**Actions 탭에서 진행 상황 확인:**
1. `https://github.com/TlesMes/TeamMoa-Refactor/actions`
2. 최신 워크플로우 클릭
3. 3개 Job 확인:
   - ✅ Run Tests (테스트 + 문서 자동 업데이트 포함)
   - ✅ Build and Push Docker Image
   - 🔄 Deploy to ALB (Rolling Update)

### 3. Deploy Job 상세 단계

**Web1 배포 (3분):**
```
📦 Deploy Web1: Deregister from Target Group
   └─ Web1을 Target Group에서 제거 (30초)
   └─ 트래픽이 Web2로만 전달됨

📦 Deploy Web1: Deploy via SSH
   └─ Docker 이미지 Pull (30초)
   └─ 컨테이너 재시작 (30초)
   └─ Health Check 3회 연속 성공 (90초)

📦 Deploy Web1: Register to Target Group
   └─ Web1을 Target Group에 다시 등록 (60초)
   └─ Target Health 확인 (healthy 되어야 함)
```

**Web2 배포 (3분):**
- Web1과 동일한 프로세스 반복

**최종 확인:**
```
✅ Verify deployment
   └─ 2개 타겟 모두 healthy 확인
   └─ 배포 완료 메시지 출력
```

### 4. 배포 로그 확인

**GitHub Actions 로그 예시:**
```
🔄 Removing Web1 from Target Group...
⏳ Waiting for connection draining (30s)...
✅ Web1 deregistered

📂 Current directory: /home/ubuntu/TeamMoa
🐳 Step 1: Pulling latest Docker image...
✅ Docker image pulled successfully

🔄 Step 2: Restarting web container...
✅ Web container restarted

⏳ Step 3: Waiting for container to start (30 seconds)...

🏥 Step 4: Health Check (3 consecutive successes required)...
Health Check Attempt 1/8...
  ✅ Container Status: healthy (1/3)
  ⏳ Waiting 15s for next check...

Health Check Attempt 2/8...
  ✅ Container Status: healthy (2/3)
  ⏳ Waiting 15s for next check...

Health Check Attempt 3/8...
  ✅ Container Status: healthy (3/3)

🎉 Health Check PASSED (3 consecutive successes)

✅ Deployment Successful!

🔄 Adding Web1 back to Target Group...
⏳ Waiting for Target to become healthy (60s)...
Web1 Target Health: healthy
✅ Web1 is healthy and serving traffic
```

---

## Health Check 설정

### Docker Container Health Check

**`docker-compose.prod.yml` 설정:**
```yaml
web:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
    interval: 30s       # ❌ 배포 시에는 15s로 변경 권장
    timeout: 10s
    retries: 3
    start_period: 60s
```

### 배포 스크립트 Health Check

**`scripts/deploy_web_server.sh` 로직:**
```bash
SUCCESS_COUNT=0
REQUIRED_SUCCESSES=3  # 3회 연속 성공 필요
MAX_ATTEMPTS=8        # 최대 8회 시도 (2분)
INTERVAL=15           # 15초 간격

for attempt in $(seq 1 $MAX_ATTEMPTS); do
    CONTAINER_STATUS=$(docker inspect --format='{{.State.Health.Status}}' teammoa_web_prod)

    if [ "$CONTAINER_STATUS" = "healthy" ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))

        if [ $SUCCESS_COUNT -ge $REQUIRED_SUCCESSES ]; then
            echo "✅ Health Check PASSED"
            break
        fi
    else
        SUCCESS_COUNT=0  # 실패 시 카운트 리셋
    fi

    sleep $INTERVAL
done
```

**설정 기준:**
- **Timeout**: 30초 (각 요청이 응답할 때까지 대기)
- **Interval**: 15초 (요청 간격)
- **Healthy threshold**: 3회 연속 성공
- **Unhealthy threshold**: 3~5회 연속 실패 (Docker Compose 설정)
- **총 대기 시간**: 최대 2분 (8회 × 15초)

### ALB Target Group Health Check

**AWS Console 설정 확인:**
1. EC2 → Target Groups → teammoa-tg
2. Health checks 탭 확인:
   ```
   Protocol: HTTP
   Path: /health/
   Port: traffic port (80)
   Healthy threshold: 3 consecutive checks
   Unhealthy threshold: 3 consecutive checks
   Timeout: 30 seconds
   Interval: 30 seconds
   Success codes: 200
   ```

---

## 트러블슈팅

### ❌ 문제 1: Web1 배포 실패 (Health Check 실패)

**증상:**
```
❌ Health Check FAILED after 8 attempts
Container Status: unhealthy
```

**원인:**
- Django 애플리케이션 시작 실패
- `/health/` 엔드포인트 응답 안 함
- DB/Redis 연결 실패

**해결 방법:**
```bash
# 1. EC2-Web1에 SSH 접속
ssh -i ~/.ssh/teammoa-key.pem ubuntu@<EC2_WEB1_HOST>

# 2. 컨테이너 로그 확인
docker logs teammoa_web_prod --tail 100

# 3. Health 엔드포인트 직접 테스트
curl http://localhost:8000/health/

# 4. 컨테이너 상태 확인
docker compose -f docker-compose.prod.yml ps

# 5. 수동 재시작
docker compose -f docker-compose.prod.yml restart web
```

**예방:**
- 로컬/Staging 환경에서 충분히 테스트
- DB Migration 먼저 실행
- `.env` 파일 동기화 확인

---

### ❌ 문제 2: Target Group 등록 실패

**증상:**
```
❌ Web1 failed to become healthy in Target Group
Web1 Target Health: unhealthy
```

**원인:**
- Security Group에서 ALB → Web 서버 통신 차단
- Nginx가 Port 80에서 응답 안 함
- `/health/` 엔드포인트가 200 응답하지 않음

**해결 방법:**
```bash
# 1. Security Group 확인
aws ec2 describe-security-groups \
    --group-ids <WEB_SECURITY_GROUP_ID> \
    --query "SecurityGroups[0].IpPermissions"

# 2. ALB → Web 서버 통신 허용 확인
# Inbound rule: HTTP (80) from ALB Security Group

# 3. Nginx 상태 확인
docker exec -it teammoa_nginx_prod curl http://localhost/health/

# 4. Target Health 직접 확인
aws elbv2 describe-target-health \
    --target-group-arn <TARGET_GROUP_ARN>
```

---

### ❌ 문제 3: 배포 중 전체 서비스 다운

**증상:**
- Web1 배포 중 Web2도 다운됨
- 사용자가 502 Bad Gateway 경험

**원인:**
- DB 서버 다운 (Web1, Web2가 모두 DB 공유)
- Redis 연결 끊김
- 네트워크 문제

**해결 방법:**
```bash
# 1. DB 서버 확인 (DB는 별도 EC2 또는 RDS)
ssh ubuntu@<EC2_DB_HOST>
docker ps | grep mysql

# 2. Redis 확인
docker ps | grep redis

# 3. 긴급 복구: 이전 버전으로 롤백
docker compose -f docker-compose.prod.yml pull web
docker tag tlesmes/teammoa-web:latest tlesmes/teammoa-web:rollback
docker pull tlesmes/teammoa-web:<previous-sha>
docker tag tlesmes/teammoa-web:<previous-sha> tlesmes/teammoa-web:latest
docker compose -f docker-compose.prod.yml up -d web
```

---

### ❌ 문제 4: GitHub Actions IP가 Security Group에 남아있음

**증상:**
```
Error: InvalidPermission.Duplicate
```

**원인:**
- 이전 배포 실패 시 IP 제거 안 됨
- Security Group에 중복 rule 생성 시도

**해결 방법:**
```bash
# 1. 현재 Security Group rules 확인
aws ec2 describe-security-groups \
    --group-ids <WEB_SECURITY_GROUP_ID> \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`22\`]"

# 2. 수동으로 제거
aws ec2 revoke-security-group-ingress \
    --group-id <WEB_SECURITY_GROUP_ID> \
    --protocol tcp \
    --port 22 \
    --cidr <OLD_GITHUB_ACTIONS_IP>/32
```

**예방:**
- CI/CD 파일에서 `if: always()` 사용 (이미 적용됨)
- `continue-on-error: true` 사용 (이미 적용됨)

---

## 테스트 통계 자동 업데이트

### 📊 자동 문서 업데이트 기능

**개요:**
- 테스트 실행 후 테스트 통계를 자동으로 문서에 반영
- `README.md`, `CLAUDE.md`, `docs/technical/testing.md` 등 자동 업데이트
- `[skip ci]` 태그로 무한 루프 방지

### 🔄 동작 방식

**1. 테스트 통계 생성:**
```bash
# pytest 실행 시 --generate-stats 플래그로 통계 생성
pytest -v --tb=short --generate-stats

# 결과: test_stats.json 생성 (gitignore에 포함)
{
  "accounts": {"service": 18, "api": 0, "ssr": 10, "total": 28},
  "teams": {"service": 51, "api": 12, "ssr": 15, "total": 78},
  ...
}
```

**2. 문서 자동 업데이트:**
```bash
# scripts/update_test_docs.py 실행
python scripts/update_test_docs.py

# AUTO 마커가 있는 부분만 업데이트
# <!-- AUTO:TEST_COUNT --> 249 → 새로운 테스트 수
# <!-- AUTO-GENERATED-TEST-STATS:START -->
| 앱 | 서비스 | API | SSR | 합계 |
|---|---------|-----|-----|------|
| Accounts | 18 | - | 10 | 28 |
| Teams | 53 | 19 | 15 | 87 |
| Members | 32 | 16 | 3 | 51 |
| Schedules | 12 | 13 | 9 | 34 |
| Shares | 20 | - | 13 | 33 |
| Mindmaps | 16 | 8 | 7 | 31 |
| **총계** | **151** | **56** | **57** | **264** |
<!-- AUTO-GENERATED-TEST-STATS:END -->
```

### ⚠️ 주의사항

**무한 루프 방지:**
- 문서 업데이트 커밋에 `[skip ci]` 태그 포함
- `paths-ignore`에 `docs/**`, `*.md` 추가 (이중 안전장치)

**권한 설정:**
```yaml
jobs:
  test:
    permissions:
      contents: write  # docs 커밋 및 푸시 권한 필요
```

**gitignore:**
```
test_stats.json  # 자동 생성 파일, git에 포함하지 않음
```

### 📁 관련 파일

- **스크립트**: `scripts/update_test_docs.py`
- **워크플로우**: `.github/workflows/ci-cd.yml` (106-127번 라인)
- **수동 실행**: `.github/workflows/update-test-docs.yml`
- **마커 포함 문서**: `README.md`, `CLAUDE.md`, `docs/technical/testing.md`, `docs/README.md`

---

## 배포 모니터링

### 📊 CloudWatch 메트릭 확인

**배포 전후 비교:**
1. **CloudWatch → Metrics → ApplicationELB**
2. **메트릭 선택:**
   - `RequestCount` (요청 수)
   - `TargetResponseTime` (응답 시간)
   - `HTTPCode_Target_2XX_Count` (성공 응답)
   - `HTTPCode_Target_5XX_Count` (서버 에러)
   - `HealthyHostCount` (정상 타겟 수)

**정상 배포 패턴:**
```
HealthyHostCount:
  2 → 1 (Web1 배포 중) → 2 → 1 (Web2 배포 중) → 2

RequestCount:
  계속 유지 (다운타임 없음)

HTTPCode_Target_5XX_Count:
  0 유지 (에러 없음)
```

### 🔔 배포 알림 (선택 사항)

**Slack Webhook 추가:**
```yaml
# .github/workflows/ci-cd.yml 에 추가

- name: Notify Slack on Failure
  if: failure()
  uses: slackapi/slack-github-action@v1.24.0
  with:
    payload: |
      {
        "text": "❌ TeamMoa 배포 실패",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "배포가 실패했습니다.\n*Commit:* ${{ github.sha }}\n*Branch:* ${{ github.ref }}"
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 배포 체크리스트

**배포 전:**
- [ ] 로컬에서 테스트 통과 확인 (`pytest`)
- [ ] GitHub Secrets 모두 등록됨
- [ ] EC2-Web1, Web2에 `deploy_web_server.sh` 스크립트 존재
- [ ] Target Group에 2개 타겟 모두 healthy

**배포 중:**
- [ ] GitHub Actions 로그 실시간 확인
- [ ] CloudWatch 메트릭 모니터링
- [ ] `https://teammoa.shop` 접속 테스트

**배포 후:**
- [ ] 2개 타겟 모두 healthy 확인
- [ ] 주요 기능 수동 테스트 (로그인, TODO, 마인드맵)
- [ ] 에러 로그 확인 (`docker logs`)

---

## 다음 단계: 개선 방안

### 1. Blue-Green Deployment (고급)
- Web1 = Blue, Web2 = Green
- 트래픽 전환 시간 최소화

### 2. Canary Deployment (고급)
- Web1에만 배포 → 10% 트래픽
- 에러 없으면 100%로 증가

### 3. 자동 롤백
- Health Check 실패 시 이전 이미지로 자동 복구

### 4. 배포 알림
- Slack/Discord/Email 연동
- CloudWatch Alarm 설정

---

**작성일**: 2025.12.12
**버전**: 1.0
**관련 문서**:
- [ALB 구축 가이드](./alb_deployment_guide.md)
- [ALB 웹 콘솔 모니터링 가이드](./alb_web_console_guide.md)
