#!/bin/bash

# TeamMoa Web Server Deployment Script
# ALB 환경에서 단일 Web 서버(Web1 또는 Web2)를 배포하는 스크립트
#
# Usage:
#   ./deploy_web_server.sh
#
# 이 스크립트는 GitHub Actions에서 SSH로 실행됩니다.

set -e  # 에러 발생 시 즉시 중단

echo "=================================================="
echo "TeamMoa Web Server Deployment"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Hostname: $(hostname)"
echo "=================================================="
echo ""

# 1. 작업 디렉토리 이동
cd ~/TeamMoa || { echo "❌ TeamMoa directory not found"; exit 1; }

echo "📂 Current directory: $(pwd)"
echo ""

# 2. Docker 이미지 Pull
echo "🐳 Step 1: Pulling latest Docker image..."

# Docker Compose 파일 자동 감지
if [ -f "docker-compose.prod.yml" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
elif [ -f "docker-compose.web.yml" ]; then
    COMPOSE_FILE="docker-compose.web.yml"
else
    echo "❌ Docker Compose file not found"
    exit 1
fi

echo "Using Docker Compose file: $COMPOSE_FILE"
docker compose -f $COMPOSE_FILE pull web

if [ $? -ne 0 ]; then
    echo "❌ Failed to pull Docker image"
    exit 1
fi

echo "✅ Docker image pulled successfully"
echo ""

# 3. Web 컨테이너 재시작 (Nginx는 유지)
echo "🔄 Step 2: Restarting web container..."
docker compose -f $COMPOSE_FILE up -d web

if [ $? -ne 0 ]; then
    echo "❌ Failed to restart web container"
    exit 1
fi

echo "✅ Web container restarted"
echo ""

# 4. 초기 대기 (컨테이너 부팅 시간)
echo "⏳ Step 3: Waiting for container to start (30 seconds)..."
sleep 30

# 5. Health Check (안정적 기준 적용)
# Healthy threshold: 3회 연속 성공
# Interval: 15초
# Timeout: 30초 (각 요청)
# 총 대기 시간: 최대 2분

echo "🏥 Step 4: Health Check (3 consecutive successes required)..."
echo ""

SUCCESS_COUNT=0
REQUIRED_SUCCESSES=3
MAX_ATTEMPTS=8  # 최대 8회 시도 (2분)
INTERVAL=15     # 15초 간격

for attempt in $(seq 1 $MAX_ATTEMPTS); do
    echo "Health Check Attempt $attempt/$MAX_ATTEMPTS..."

    # Docker container health 확인
    CONTAINER_STATUS=$(docker inspect --format='{{.State.Health.Status}}' teammoa_web_prod 2>/dev/null || echo "unknown")

    if [ "$CONTAINER_STATUS" = "healthy" ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        echo "  ✅ Container Status: healthy ($SUCCESS_COUNT/$REQUIRED_SUCCESSES)"

        # 3회 연속 성공 시 통과
        if [ $SUCCESS_COUNT -ge $REQUIRED_SUCCESSES ]; then
            echo ""
            echo "🎉 Health Check PASSED (3 consecutive successes)"
            break
        fi
    else
        SUCCESS_COUNT=0  # 실패 시 카운트 리셋
        echo "  ⚠️  Container Status: $CONTAINER_STATUS (resetting counter)"
    fi

    # 마지막 시도가 아니면 대기
    if [ $attempt -lt $MAX_ATTEMPTS ]; then
        echo "  ⏳ Waiting ${INTERVAL}s for next check..."
        sleep $INTERVAL
        echo ""
    fi
done

# 6. 최종 검증
if [ $SUCCESS_COUNT -lt $REQUIRED_SUCCESSES ]; then
    echo ""
    echo "❌ Health Check FAILED after $MAX_ATTEMPTS attempts"
    echo ""
    echo "📋 Container Status:"
    docker compose -f $COMPOSE_FILE ps
    echo ""
    echo "📋 Container Logs (last 50 lines):"
    docker logs teammoa_web_prod --tail 50 2>&1 || echo "No logs available"
    echo ""
    echo "❌ Deployment FAILED"
    exit 1
fi

# 7. 최종 상태 확인
echo ""
echo "📊 Final Container Status:"
docker compose -f $COMPOSE_FILE ps

echo ""
echo "=================================================="
echo "✅ Deployment Successful!"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

exit 0
