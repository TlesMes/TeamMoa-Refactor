# Load Testing Guide

> **AWS ALB + Multi-AZ 인프라 부하 테스트 문서**

## 📁 파일 구조

- **[load-test-report.md](./load-test-report.md)** - 부하 테스트 결과 전체 리포트
- **[summary.txt](./summary.txt)** - 4회 테스트 결과 요약 (원본 데이터)
- **[locustfile.py](./locustfile.py)** - Locust 테스트 시나리오 스크립트
- **[config.py](./config.py)** - 테스트 설정 파일
- **[create_test_account.py](./create_test_account.py)** - 테스트 계정 생성 스크립트

## 🎯 테스트 개요

**일시**: 2025년 12월 16일
**전략**: 점진적 부하 증가 (20명 → 50명 → 100명 → 150명)
**총 요청 수**: 57,232건 (4회 반복 테스트)

## 📊 핵심 결과

| 지표 | 목표 (SLA) | 측정값 | 달성 여부 |
|------|----------|--------|----------|
| 95%ile 응답 시간 | ≤ 500ms | **70ms** | ✅ **86% 향상** |
| 평균 응답 시간 | - | **52ms** | ✅ **안정적** |
| 에러율 | ≤ 1% | **0.16%** | ✅ **84% 향상** |
| 최대 RPS | ≥ 10 | **40.34** | ✅ **303% 초과 달성** |

## 🚀 테스트 실행 방법

```bash
# 1. Locust 설치
pip install locust websocket-client

# 2. 테스트 계정 생성
python manage.py shell < create_test_account.py

# 3. 설정 확인
# config.py에서 ALB_URL 확인

# 4. Locust 실행
locust -f locustfile.py --host https://teammoa.shop

# 5. 브라우저에서 접속
# http://localhost:8089
```

## 📚 관련 문서

- **[프로젝트 README](../../../README.md)** - 프로덕션 성능 검증 섹션
- **[Infrastructure 문서](../../portfolio/infrastructure.md)** - 부하 테스트 및 성능 검증 섹션
- **[ALB 구축 가이드](../alb_deployment_guide.md)** - AWS ALB 설정 방법

---

**작성일**: 2025년 12월 16일
**테스트 환경**: AWS ALB + EC2 t3.micro × 2대 (Multi-AZ)
