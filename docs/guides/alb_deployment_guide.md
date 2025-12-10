# AWS Application Load Balancer 구축 가이드

> **TeamMoa 프로젝트에 ALB + Multi-AZ 고가용성 아키텍처 구축**
> 3-Tier 아키텍처: Web(2대) + DB(1대) + ALB
>
> 단계별 실습 가이드 (예상 소요 시간: 6~8시간)

---

## 🏗️ 아키텍처 개요

### 변경 전 (현재)
```
단일 EC2 (3.34.102.12)
├── MySQL (Docker)
├── Redis (Docker)
├── Django (Docker)
└── Nginx (Docker)
```

### 변경 후 (ALB + 3-Tier)
```
Internet
    │
    ▼
ALB (HTTPS:443)
    │
    ├─────────────────────┬─────────────────────┐
    │                     │                     │
Public Subnet A      Public Subnet B      Private Subnet
(ap-northeast-2a)    (ap-northeast-2b)    (ap-northeast-2a)
    │                     │                     │
EC2-Web1              EC2-Web2              EC2-DB
├── Django            ├── Django            ├── MySQL
└── Nginx             └── Nginx             └── Redis
    │                     │                     ▲
    └─────────────────────┴─────────────────────┘
              Private IP 통신 (3306, 6379)
```

**네트워크 구조**:
```
VPC: 10.0.0.0/16
├── Public Subnet A: 10.0.1.0/24 (ap-northeast-2a)
│   ├── ALB
│   ├── EC2-Web1
│   └── NAT Gateway
├── Public Subnet B: 10.0.2.0/24 (ap-northeast-2b)
│   ├── ALB
│   └── EC2-Web2
└── Private Subnet: 10.0.10.0/24 (ap-northeast-2a)
    └── EC2-DB ← 인터넷 직접 노출 안 됨
```

**핵심 원칙**:
- ✅ **Web 서버 2대 (Public)**: Stateless, 로드밸런싱 가능
- ✅ **DB 서버 1대 (Private)**: 데이터 일관성 보장, 인터넷 차단
- ✅ **Web ↔ DB 통신**: VPC 내부 Private IP (10.0.10.x)
- ✅ **DB 인터넷 접속**: NAT Gateway 통해서만 (Docker pull, 업데이트)

---

## 📋 목차
1. [사전 준비](#사전-준비)
2. [아키텍처 설계 결정](#아키텍처-설계-결정)
3. [VPC 및 Subnet 구성](#vpc-및-subnet-구성)
4. [EC2-DB 분리 구성](#ec2-db-분리-구성)
5. [EC2-Web 2개 구성](#ec2-web-2개-구성)
6. [ALB 생성 및 설정](#alb-생성-및-설정)
7. [ACM SSL 인증서 발급](#acm-ssl-인증서-발급)
8. [Security Group 구성](#security-group-구성)
9. [Django 설정 변경](#django-설정-변경)
10. [CI/CD 파이프라인 수정](#cicd-파이프라인-수정)
11. [테스트 및 검증](#테스트-및-검증)
12. [트러블슈팅](#트러블슈팅)

---

## 사전 준비

### 필요한 정보 수집

```bash
# 현재 EC2 정보
현재 EC2 인스턴스 ID: i-xxxxxxxxxxxxxxxxx
현재 Elastic IP: 3.34.102.12
현재 Region: ap-northeast-2 (Seoul)
현재 AZ: ap-northeast-2a
도메인: teammoa.duckdns.org
```

### AWS CLI 설치 및 설정

```bash
# AWS CLI 설치 확인
aws --version

# AWS CLI 설정 (아직 안 했다면)
aws configure
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region: ap-northeast-2
# Default output format: json
```

### IAM 권한 확인

필요한 IAM 권한:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "elasticloadbalancing:*",
        "acm:*",
        "route53:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## VPC 및 Subnet 구성

### 1. VPC 생성 (기존 VPC 있다면 스킵)

```bash
# VPC 생성
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=teammoa-vpc}]'

# 출력에서 VPC ID 기록
# VpcId: vpc-xxxxxxxxxxxxxxxxx
VPC_ID="vpc-xxxxxxxxxxxxxxxxx"

# DNS 호스트 이름 활성화 (ALB 필수)
aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-hostnames
```

### 2. Internet Gateway 생성 및 연결

```bash
# Internet Gateway 생성
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=teammoa-igw}]'

IGW_ID="igw-xxxxxxxxxxxxxxxxx"

# VPC에 연결
aws ec2 attach-internet-gateway \
  --vpc-id $VPC_ID \
  --internet-gateway-id $IGW_ID
```

### 3. Public Subnet 2개 생성 (Multi-AZ, ALB + Web 서버용)

```bash
# Public Subnet A (AZ-A)
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone ap-northeast-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=teammoa-public-a}]'

PUBLIC_SUBNET_A="subnet-xxxxxxxxxxxxxxxxx"

# Public Subnet B (AZ-B)
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone ap-northeast-2b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=teammoa-public-b}]'

PUBLIC_SUBNET_B="subnet-xxxxxxxxxxxxxxxxx"

# 자동 공인 IP 할당 활성화
aws ec2 modify-subnet-attribute \
  --subnet-id $PUBLIC_SUBNET_A \
  --map-public-ip-on-launch

aws ec2 modify-subnet-attribute \
  --subnet-id $PUBLIC_SUBNET_B \
  --map-public-ip-on-launch
```

### 4. Private Subnet 1개 생성 (EC2-DB 전용)

```bash
# Private Subnet A (AZ-A, DB 서버용)
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.10.0/24 \
  --availability-zone ap-northeast-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=teammoa-private-db}]'

PRIVATE_SUBNET_DB="subnet-xxxxxxxxxxxxxxxxx"

# 참고: EC2-DB는 1대만 배치하므로 Private Subnet도 1개만 필요
```

### 5. NAT Gateway 생성 (Private Subnet용)

```bash
# Elastic IP 할당 (NAT Gateway용)
aws ec2 allocate-address --domain vpc

# 출력에서 AllocationId 기록
NAT_EIP_ALLOC_ID="eipalloc-xxxxxxxxxxxxxxxxx"

# NAT Gateway 생성 (Public Subnet A에 배치)
aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_A \
  --allocation-id $NAT_EIP_ALLOC_ID \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=teammoa-nat}]'

NAT_GATEWAY_ID="nat-xxxxxxxxxxxxxxxxx"

# NAT Gateway 생성 완료 대기 (2~5분 소요)
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GATEWAY_ID
echo "NAT Gateway 생성 완료!"
```

### 6. Route Table 설정

```bash
# Public Route Table 생성
aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=teammoa-public-rt}]'

PUBLIC_RT_ID="rtb-xxxxxxxxxxxxxxxxx"

# Internet Gateway로 라우팅
aws ec2 create-route \
  --route-table-id $PUBLIC_RT_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID

# Public Subnet에 연결
aws ec2 associate-route-table \
  --subnet-id $PUBLIC_SUBNET_A \
  --route-table-id $PUBLIC_RT_ID

aws ec2 associate-route-table \
  --subnet-id $PUBLIC_SUBNET_B \
  --route-table-id $PUBLIC_RT_ID

# Private Route Table 생성
aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=teammoa-private-rt}]'

PRIVATE_RT_ID="rtb-xxxxxxxxxxxxxxxxx"

# NAT Gateway로 라우팅 (EC2-DB가 인터넷 접속용)
aws ec2 create-route \
  --route-table-id $PRIVATE_RT_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GATEWAY_ID

# Private Subnet에 연결
aws ec2 associate-route-table \
  --subnet-id $PRIVATE_SUBNET_DB \
  --route-table-id $PRIVATE_RT_ID
```

---

## 아키텍처 설계 결정

### Option 1: EC2-DB 단일 인스턴스 (Private Subnet) ⭐ 이 가이드 선택
**장점**:
- DB가 Private Subnet에 위치 (보안 강화)
- Web 서버만 DB 접속 가능 (Security Group)
- 설정 복잡도 적절함 (학습 효과 좋음)

**단점**:
- NAT Gateway 비용 발생 (월 $32)
- DB 단일 장애점 (SPOF)

**예상 비용**:
- 프리티어 기간: 월 $54 (ALB $22 + NAT $32)
- 프리티어 종료: 월 $87 (ALB $22 + NAT $32 + EC2 3대 $33)

---

### Option 2: RDS Multi-AZ
**장점**:
- 고가용성 (자동 Failover)
- 자동 백업, 패치
- 관리 부담 감소

**단점**:
- 비용 높음 (RDS db.t3.micro: 월 $25)
- Redis 별도 ElastiCache 필요 (월 $17)

**예상 비용**:
- 프리티어 종료 후: 월 $80~$100

---

### 📌 이 가이드의 선택: **Option 1 (EC2-DB 단일)**
- 학습 목적 + 비용 효율성 우선
- 나중에 RDS 전환 가능 (마이그레이션 가이드 별도 작성)

---

## EC2-DB 분리 구성

### 1. 현재 EC2 상태 확인

```bash
# 현재 EC2 정보 (모놀리식 서버)
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=teammoa-web" \
  --query 'Reservations[0].Instances[0].[InstanceId,PublicIpAddress,PrivateIpAddress]'

# 출력 예시:
# i-0abcdef1234567890, 3.34.102.12, 10.0.1.10
```

### 2. Docker Compose 분리 파일 사용

프로젝트에 이미 분리된 파일이 준비되어 있습니다:
- **`docker-compose.web.yml`**: Web 서버용 (Django + Nginx)
- **`docker-compose.db.yml`**: DB 서버용 (MySQL + Redis)

**핵심 차이점**:
| 파일 | 포함 서비스 | 사용 서버 |
|------|------------|----------|
| `docker-compose.web.yml` | web, nginx | EC2-Web1, EC2-Web2 |
| `docker-compose.db.yml` | db, redis | EC2-DB |
| `docker-compose.prod.yml` | 전체 (기존) | 단일 서버 (레거시) |

**주요 설정 차이**:
```yaml
# docker-compose.db.yml의 핵심 설정
db:
  command: --bind-address=0.0.0.0  # 외부 접속 허용
  ports:
    - "3306:3306"  # Web 서버 접속용

redis:
  command: redis-server --bind 0.0.0.0  # 외부 접속 허용
  ports:
    - "6379:6379"  # Web 서버 접속용
```

### 3. 현재 EC2를 Private Subnet으로 이동

현재 EC2는 Public Subnet에 있으므로, Private Subnet으로 이동하거나 새로 생성해야 합니다.

#### Option A: 현재 EC2를 그대로 사용 (Public Subnet 유지)
- 비용 절감 (Elastic IP 재활용)
- 단점: DB가 Public IP 보유 (Security Group으로만 보호)

#### Option B: Private Subnet에 새 EC2-DB 생성 ⭐ 권장
```bash
# 현재 EC2의 AMI 생성 (백업)
aws ec2 create-image \
  --instance-id i-xxxxxxxxxxxxxxxxx \
  --name "teammoa-db-backup-$(date +%Y%m%d)" \
  --description "TeamMoa DB backup before migration" \
  --no-reboot

AMI_ID="ami-xxxxxxxxxxxxxxxxx"

# AMI 생성 완료 대기
aws ec2 wait image-available --image-ids $AMI_ID

# Private Subnet에 새 EC2-DB 생성
aws ec2 run-instances \
  --image-id $AMI_ID \
  --count 1 \
  --instance-type t3.micro \
  --key-name YOUR_KEY_PAIR_NAME \
  --security-group-ids $DB_SG_ID \
  --subnet-id $PRIVATE_SUBNET_DB \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=teammoa-db}]' \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]'

EC2_DB_ID="i-xxxxxxxxxxxxxxxxx"

# 인스턴스 시작 대기
aws ec2 wait instance-running --instance-ids $EC2_DB_ID

# Private IP 확인 (Public IP는 없음)
aws ec2 describe-instances \
  --instance-ids $EC2_DB_ID \
  --query 'Reservations[0].Instances[0].PrivateIpAddress'

DB_PRIVATE_IP="10.0.10.x"
```

### 4. EC2-DB에 SSH 접속 (Bastion 방식)

Private Subnet의 EC2는 직접 SSH 불가. 임시로 Web 서버를 경유합니다:

```bash
# EC2-Web1을 Bastion으로 사용
ssh -i ~/.ssh/your-key.pem -J ubuntu@EC2_WEB1_PUBLIC_IP ubuntu@$DB_PRIVATE_IP

# 또는 SSH Config 설정 (~/.ssh/config)
Host teammoa-db
  HostName 10.0.10.x
  User ubuntu
  ProxyJump ubuntu@EC2_WEB1_PUBLIC_IP
  IdentityFile ~/.ssh/your-key.pem

# 이후 간편 접속
ssh teammoa-db
```

### 5. EC2-DB 초기 설정

```bash
# SSH 접속 (Bastion 경유)
ssh teammoa-db

# 기존 컨테이너 중지 (AMI에서 복제된 경우)
cd ~/TeamMoa
docker compose -f docker-compose.prod.yml down

# docker-compose.db.yml 파일 확인
cat docker-compose.db.yml

# .env 파일 수정 (DB_HOST는 localhost)
nano .env

# DB 컨테이너만 시작
docker compose -f docker-compose.db.yml up -d

# 상태 확인
docker compose -f docker-compose.db.yml ps
```

---

## EC2-Web 2개 구성

### 1. AMI 생성 (백업)

```bash
# Security Group 생성 (임시, 나중에 수정)
aws ec2 create-security-group \
  --group-name teammoa-ec2-sg \
  --description "Security group for TeamMoa EC2 instances" \
  --vpc-id $VPC_ID

EC2_SG_ID="sg-xxxxxxxxxxxxxxxxx"

# SSH 포트 임시 개방 (나중에 제거)
aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# EC2-2 인스턴스 생성
aws ec2 run-instances \
  --image-id $AMI_ID \
  --count 1 \
  --instance-type t3.micro \
  --key-name YOUR_KEY_PAIR_NAME \
  --security-group-ids $EC2_SG_ID \
  --subnet-id $PUBLIC_SUBNET_B \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=teammoa-web-2}]' \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]'

# 출력에서 Instance ID 기록
EC2_2_ID="i-xxxxxxxxxxxxxxxxx"

# 인스턴스 시작 대기
aws ec2 wait instance-running --instance-ids $EC2_2_ID
echo "EC2-2 시작 완료!"

# Public IP 확인
aws ec2 describe-instances \
  --instance-ids $EC2_2_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress'

EC2_2_IP="x.x.x.x"
```

### 4. Elastic IP 할당 (EC2-2)

```bash
# Elastic IP 할당
aws ec2 allocate-address --domain vpc

# 출력에서 AllocationId 기록
EIP_2_ALLOC_ID="eipalloc-xxxxxxxxxxxxxxxxx"
EIP_2_ADDRESS="x.x.x.x"

# EC2-2에 연결
aws ec2 associate-address \
  --instance-id $EC2_2_ID \
  --allocation-id $EIP_2_ALLOC_ID

echo "EC2-2 Elastic IP: $EIP_2_ADDRESS"
```

### 5. EC2-2 초기 설정

```bash
# SSH 접속
ssh -i ~/.ssh/your-key.pem ubuntu@$EIP_2_ADDRESS

# 서버에서 실행
# 1. 도커 컨테이너 상태 확인
docker ps

# 2. .env 파일 확인 및 수정 (필요 시)
cd ~/TeamMoa
nano .env

# 3. 컨테이너 재시작
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# 4. Health Check 확인
curl http://localhost:8000/health/

# 5. 로그 확인
docker compose -f docker-compose.prod.yml logs web
```

---

## ALB 생성 및 설정

### 1. Security Group 생성 (ALB용)

```bash
# ALB Security Group 생성
aws ec2 create-security-group \
  --group-name teammoa-alb-sg \
  --description "Security group for TeamMoa ALB" \
  --vpc-id $VPC_ID

ALB_SG_ID="sg-xxxxxxxxxxxxxxxxx"

# HTTP 허용 (80)
aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# HTTPS 허용 (443)
aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### 2. ALB 생성

```bash
# Application Load Balancer 생성
aws elbv2 create-load-balancer \
  --name teammoa-alb \
  --subnets $PUBLIC_SUBNET_A $PUBLIC_SUBNET_B \
  --security-groups $ALB_SG_ID \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --tags Key=Name,Value=teammoa-alb

# 출력에서 ARN 기록
ALB_ARN="arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/app/teammoa-alb/1234567890abcdef"
ALB_DNS="teammoa-alb-1234567890.ap-northeast-2.elb.amazonaws.com"

echo "ALB DNS: $ALB_DNS"
```

### 3. Target Group 생성

```bash
# Target Group 생성
aws elbv2 create-target-group \
  --name teammoa-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $VPC_ID \
  --health-check-protocol HTTP \
  --health-check-path /health/ \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --matcher HttpCode=200

# 출력에서 ARN 기록
TARGET_GROUP_ARN="arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:targetgroup/teammoa-tg/1234567890abcdef"
```

### 4. EC2 인스턴스를 Target Group에 등록

```bash
# EC2-1 등록
aws elbv2 register-targets \
  --target-group-arn $TARGET_GROUP_ARN \
  --targets Id=i-xxxxxxxxxxxxxxxxx,Port=8000

# EC2-2 등록
aws elbv2 register-targets \
  --target-group-arn $TARGET_GROUP_ARN \
  --targets Id=$EC2_2_ID,Port=8000

# Target Health 확인 (1~2분 후)
aws elbv2 describe-target-health \
  --target-group-arn $TARGET_GROUP_ARN
```

### 5. HTTP Listener 생성 (임시, HTTPS 설정 전)

```bash
# HTTP Listener 생성 (80 → Target Group)
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN

# 출력에서 Listener ARN 기록
HTTP_LISTENER_ARN="arn:aws:elasticloadbalancing:..."
```

### 6. HTTP 테스트

```bash
# ALB를 통한 접속 테스트
curl -I http://$ALB_DNS/health/

# 예상 출력:
# HTTP/1.1 200 OK
# Content-Type: application/json
```

---

## ACM SSL 인증서 발급

### 1. ACM 인증서 요청

```bash
# ACM 인증서 요청
aws acm request-certificate \
  --domain-name teammoa.duckdns.org \
  --subject-alternative-names "*.teammoa.duckdns.org" \
  --validation-method DNS \
  --region ap-northeast-2

# 출력에서 Certificate ARN 기록
CERT_ARN="arn:aws:acm:ap-northeast-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"
```

### 2. DNS 검증 레코드 확인

```bash
# 검증 레코드 확인
aws acm describe-certificate \
  --certificate-arn $CERT_ARN \
  --region ap-northeast-2 \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'

# 출력 예시:
{
  "Name": "_abc123.teammoa.duckdns.org",
  "Type": "CNAME",
  "Value": "_xyz456.acm-validations.aws."
}
```

### 3. DuckDNS에 CNAME 레코드 추가

**DuckDNS는 CNAME을 직접 지원하지 않으므로, Route 53 사용 권장**

#### Option A: Route 53 사용 (권장)

```bash
# Route 53 Hosted Zone 생성
aws route53 create-hosted-zone \
  --name teammoa.duckdns.org \
  --caller-reference $(date +%s)

# Hosted Zone ID 기록
HOSTED_ZONE_ID="Z1234567890ABC"

# ACM 검증 레코드 추가
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "_abc123.teammoa.duckdns.org",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "_xyz456.acm-validations.aws."}]
      }
    }]
  }'

# ACM 인증서 검증 완료 대기 (5~30분)
aws acm wait certificate-validated \
  --certificate-arn $CERT_ARN \
  --region ap-northeast-2

echo "ACM 인증서 발급 완료!"
```

#### Option B: DuckDNS 계속 사용 (Email 검증)

```bash
# ACM 인증서 재요청 (Email 검증)
aws acm request-certificate \
  --domain-name teammoa.duckdns.org \
  --validation-method EMAIL \
  --region ap-northeast-2

# 이메일에서 검증 링크 클릭
# (DuckDNS 등록 이메일로 발송)
```

### 4. ALB에 HTTPS Listener 추가

```bash
# HTTPS Listener 생성 (443 → Target Group)
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=$CERT_ARN \
  --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN

HTTPS_LISTENER_ARN="arn:aws:elasticloadbalancing:..."

# HTTP Listener를 HTTPS로 리디렉션 수정
aws elbv2 modify-listener \
  --listener-arn $HTTP_LISTENER_ARN \
  --default-actions Type=redirect,RedirectConfig="{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}"
```

### 5. DuckDNS DNS 레코드 변경

```bash
# DuckDNS에서 teammoa.duckdns.org를 ALB DNS로 변경
# 웹 브라우저에서: https://www.duckdns.org/update?domains=teammoa&token=YOUR_TOKEN&txt=$ALB_DNS

# 또는 curl 사용
curl "https://www.duckdns.org/update?domains=teammoa&token=YOUR_DUCKDNS_TOKEN&ip=$ALB_DNS"
```

### 6. HTTPS 테스트

```bash
# HTTPS 접속 테스트
curl -I https://teammoa.duckdns.org/health/

# 예상 출력:
# HTTP/2 200
# content-type: application/json
```

---

## Security Group 구성

### 전체 구조

```
Internet
    ↓ (HTTPS:443, HTTP:80)
ALB Security Group
    ↓ (HTTP:80)
EC2-Web Security Group (2대)
    ↓ (MySQL:3306, Redis:6379)
EC2-DB Security Group (1대)
```

### 1. ALB Security Group

```bash
# ALB Security Group 생성
aws ec2 create-security-group \
  --group-name teammoa-alb-sg \
  --description "Security group for TeamMoa ALB" \
  --vpc-id $VPC_ID

ALB_SG_ID="sg-xxxxxxxxxxxxxxxxx"

# Inbound: HTTP (80)
aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Inbound: HTTPS (443)
aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### 2. EC2-Web Security Group

```bash
# EC2-Web Security Group 생성
aws ec2 create-security-group \
  --group-name teammoa-web-sg \
  --description "Security group for TeamMoa Web servers" \
  --vpc-id $VPC_ID

WEB_SG_ID="sg-xxxxxxxxxxxxxxxxx"

# Inbound: ALB → Web:80 (Nginx)
aws ec2 authorize-security-group-ingress \
  --group-id $WEB_SG_ID \
  --protocol tcp \
  --port 80 \
  --source-group $ALB_SG_ID

# Inbound: SSH (GitHub Actions, 나중에 동적으로 추가)
# CI/CD에서 필요 시 동적으로 추가/제거
```

### 3. EC2-DB Security Group

```bash
# EC2-DB Security Group 생성
aws ec2 create-security-group \
  --group-name teammoa-db-sg \
  --description "Security group for TeamMoa Database server" \
  --vpc-id $VPC_ID

DB_SG_ID="sg-xxxxxxxxxxxxxxxxx"

# Inbound: Web → DB:3306 (MySQL)
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG_ID \
  --protocol tcp \
  --port 3306 \
  --source-group $WEB_SG_ID

# Inbound: Web → DB:6379 (Redis)
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG_ID \
  --protocol tcp \
  --port 6379 \
  --source-group $WEB_SG_ID

# Inbound: SSH (관리용, My IP만)
MY_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr $MY_IP/32
```

### 4. Security Group 적용

```bash
# EC2-DB에 적용
aws ec2 modify-instance-attribute \
  --instance-id $DB_INSTANCE_ID \
  --groups $DB_SG_ID

# EC2-Web1에 적용
aws ec2 modify-instance-attribute \
  --instance-id $WEB_1_INSTANCE_ID \
  --groups $WEB_SG_ID

# EC2-Web2에 적용
aws ec2 modify-instance-attribute \
  --instance-id $WEB_2_INSTANCE_ID \
  --groups $WEB_SG_ID
```

---

## Django 설정 변경

### 1. `.env` 파일 수정

#### EC2-Web1, EC2-Web2용 `.env`

```bash
# Database Host (EC2-DB Private IP)
DB_HOST=10.0.1.10  # EC2-DB Private IP
DB_PORT=3306
DB_NAME=teammoa_db
DB_USER=teammoa_user
DB_PASSWORD=tobiz3909
DB_CONN_MAX_AGE=600

# Redis Settings (EC2-DB Private IP)
REDIS_HOST=10.0.1.10  # EC2-DB Private IP
REDIS_PORT=6379
REDIS_PASSWORD=Redis2024!StrongPass

# Django Settings
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,teammoa.duckdns.org,web

# Security (HTTPS는 ALB에서 처리)
SECURE_SSL_REDIRECT=False  # Nginx에서 처리
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# CORS
CORS_ALLOWED_ORIGINS=https://teammoa.duckdns.org
```

#### EC2-DB용 `.env`

```bash
# Database Settings (Local)
DB_HOST=localhost
DB_ROOT_PASSWORD=RootPass2024!Secure
DB_NAME=teammoa_db
DB_USER=teammoa_user
DB_PASSWORD=tobiz3909

# Redis Settings (Local)
REDIS_PASSWORD=Redis2024!StrongPass
```

### 2. `TeamMoa/settings/prod.py` 수정

```python
# TeamMoa/settings/prod.py

ALLOWED_HOSTS = env.list(
    'ALLOWED_HOSTS',
    default=['localhost', '127.0.0.1', 'teammoa.duckdns.org']
)

# Database (외부 EC2-DB 연결)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),  # EC2-DB Private IP
        'PORT': env('DB_PORT', default='3306'),
        'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', default=600),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Redis (외부 EC2-DB 연결)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(env('REDIS_HOST'), env.int('REDIS_PORT', default=6379))],
            'password': env('REDIS_PASSWORD'),
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://:{env('REDIS_PASSWORD')}@{env('REDIS_HOST')}:{env.int('REDIS_PORT', default=6379)}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# HTTPS는 ALB에서 처리
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # ALB가 처리하므로 Django에서는 False

CSRF_TRUSTED_ORIGINS = [
    'https://teammoa.duckdns.org',
]
```

### 3. Health Check 엔드포인트 개선

```python
# config/urls.py

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

def health_check(request):
    """
    ALB Target Group Health Check endpoint
    DB 및 Redis 연결 상태 확인
    """
    try:
        # Database 연결 확인
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    try:
        # Redis 연결 확인
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    overall_status = 200 if (db_status == "healthy" and redis_status == "healthy") else 503

    return JsonResponse({
        'status': 'healthy' if overall_status == 200 else 'unhealthy',
        'database': db_status,
        'redis': redis_status
    }, status=overall_status)

urlpatterns = [
    path('health/', health_check, name='health_check'),
    # ...
]
```

### 4. 변경 사항 배포

```bash
# 로컬에서 커밋
git add .
git commit -m "feat(infra): Add ALB support - ALLOWED_HOSTS and health check"
git push origin main

# 또는 수동 배포 (EC2-1, EC2-2 모두)
ssh ubuntu@3.34.102.12 << 'EOF'
  cd ~/TeamMoa
  git pull origin main
  docker compose -f docker-compose.prod.yml restart web
EOF

ssh ubuntu@$EIP_2_ADDRESS << 'EOF'
  cd ~/TeamMoa
  git pull origin main
  docker compose -f docker-compose.prod.yml restart web
EOF
```

---

## CI/CD 파이프라인 수정

### 1. GitHub Secrets 추가

```bash
# GitHub 리포지토리 → Settings → Secrets and variables → Actions

# 추가할 Secrets:
EC2_1_INSTANCE_ID=i-xxxxxxxxxxxxxxxxx
EC2_2_INSTANCE_ID=i-xxxxxxxxxxxxxxxxx
EC2_1_HOST=3.34.102.12
EC2_2_HOST=x.x.x.x
TARGET_GROUP_ARN=arn:aws:elasticloadbalancing:...
ALB_ARN=arn:aws:elasticloadbalancing:...
```

### 2. `.github/workflows/ci-cd.yml` 수정

```yaml
# .github/workflows/ci-cd.yml

name: CI/CD Pipeline with ALB

on:
  push:
    branches: [ main ]
    paths-ignore:
      - 'docs/**'
      - 'README.md'

env:
  DOCKER_IMAGE: tlesmes/teammoa-web

jobs:
  test:
    runs-on: ubuntu-latest
    # ... (기존 테스트 단계 동일)

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    # ... (기존 빌드 단계 동일)

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest

    steps:
      - name: Get GitHub Actions Runner IP
        id: ip
        uses: haythem/public-ip@v1.3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-2

      - name: Add GitHub Actions IP to security group
        run: |
          aws ec2 authorize-security-group-ingress \
            --group-id ${{ secrets.AWS_SECURITY_GROUP_ID }} \
            --protocol tcp \
            --port 22 \
            --cidr ${{ steps.ip.outputs.ipv4 }}/32

      # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      # Deploy to EC2-1
      # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      - name: Deregister EC2-1 from Target Group
        run: |
          aws elbv2 deregister-targets \
            --target-group-arn ${{ secrets.TARGET_GROUP_ARN }} \
            --targets Id=${{ secrets.EC2_1_INSTANCE_ID }},Port=8000

      - name: Wait for EC2-1 to drain connections
        run: |
          aws elbv2 wait target-deregistered \
            --target-group-arn ${{ secrets.TARGET_GROUP_ARN }} \
            --targets Id=${{ secrets.EC2_1_INSTANCE_ID }},Port=8000

      - name: Deploy to EC2-1
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.EC2_1_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd ~/TeamMoa
            docker compose -f docker-compose.prod.yml pull web
            docker compose -f docker-compose.prod.yml up -d web

            # Health check 통과 대기
            for i in 1 2 3 4 5; do
              if docker compose -f docker-compose.prod.yml ps | grep -q "teammoa_web.*healthy"; then
                echo "EC2-1 deployment successful!"
                exit 0
              fi
              echo "Waiting for health check... ($i/5)"
              sleep 10
            done
            echo "EC2-1 health check failed!"
            exit 1

      - name: Register EC2-1 to Target Group
        run: |
          aws elbv2 register-targets \
            --target-group-arn ${{ secrets.TARGET_GROUP_ARN }} \
            --targets Id=${{ secrets.EC2_1_INSTANCE_ID }},Port=8000

      - name: Wait for EC2-1 to be healthy
        run: |
          aws elbv2 wait target-in-service \
            --target-group-arn ${{ secrets.TARGET_GROUP_ARN }} \
            --targets Id=${{ secrets.EC2_1_INSTANCE_ID }},Port=8000

      # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      # Deploy to EC2-2
      # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      - name: Deregister EC2-2 from Target Group
        run: |
          aws elbv2 deregister-targets \
            --target-group-arn ${{ secrets.TARGET_GROUP_ARN }} \
            --targets Id=${{ secrets.EC2_2_INSTANCE_ID }},Port=8000

      - name: Wait for EC2-2 to drain connections
        run: |
          aws elbv2 wait target-deregistered \
            --target-group-arn ${{ secrets.TARGET_GROUP_ARN }} \
            --targets Id=${{ secrets.EC2_2_INSTANCE_ID }},Port=8000

      - name: Deploy to EC2-2
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.EC2_2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd ~/TeamMoa
            docker compose -f docker-compose.prod.yml pull web
            docker compose -f docker-compose.prod.yml up -d web

            # Health check 통과 대기
            for i in 1 2 3 4 5; do
              if docker compose -f docker-compose.prod.yml ps | grep -q "teammoa_web.*healthy"; then
                echo "EC2-2 deployment successful!"
                exit 0
              fi
              echo "Waiting for health check... ($i/5)"
              sleep 10
            done
            echo "EC2-2 health check failed!"
            exit 1

      - name: Register EC2-2 to Target Group
        run: |
          aws elbv2 register-targets \
            --target-group-arn ${{ secrets.TARGET_GROUP_ARN }} \
            --targets Id=${{ secrets.EC2_2_INSTANCE_ID }},Port=8000

      - name: Wait for EC2-2 to be healthy
        run: |
          aws elbv2 wait target-in-service \
            --target-group-arn ${{ secrets.TARGET_GROUP_ARN }} \
            --targets Id=${{ secrets.EC2_2_INSTANCE_ID }},Port=8000

      - name: Verify deployment
        run: |
          echo "Checking Target Group health..."
          aws elbv2 describe-target-health \
            --target-group-arn ${{ secrets.TARGET_GROUP_ARN }}

      - name: Remove GitHub Actions IP from security group
        if: always()
        run: |
          aws ec2 revoke-security-group-ingress \
            --group-id ${{ secrets.AWS_SECURITY_GROUP_ID }} \
            --protocol tcp \
            --port 22 \
            --cidr ${{ steps.ip.outputs.ipv4 }}/32
```

---

## 테스트 및 검증

### 1. Target Group Health 확인

```bash
# Target Group 상태 확인
aws elbv2 describe-target-health \
  --target-group-arn $TARGET_GROUP_ARN

# 예상 출력:
{
  "TargetHealthDescriptions": [
    {
      "Target": {
        "Id": "i-xxxxxxxxxxxxxxxxx",
        "Port": 8000
      },
      "HealthCheckPort": "8000",
      "TargetHealth": {
        "State": "healthy"
      }
    },
    {
      "Target": {
        "Id": "i-yyyyyyyyyyyyyyyyy",
        "Port": 8000
      },
      "HealthCheckPort": "8000",
      "TargetHealth": {
        "State": "healthy"
      }
    }
  ]
}
```

### 2. 로드밸런싱 테스트

```bash
# 10번 요청하여 분산 확인
for i in {1..10}; do
  curl -s https://teammoa.duckdns.org/health/ | jq '.status'
done

# EC2 로그에서 요청 확인
ssh ubuntu@3.34.102.12 "docker logs teammoa_web_prod --tail 20"
ssh ubuntu@$EIP_2_ADDRESS "docker logs teammoa_web_prod --tail 20"
```

### 3. 무중단 배포 테스트

```bash
# Terminal 1: 연속 요청
while true; do
  curl -s -o /dev/null -w "%{http_code} " https://teammoa.duckdns.org/
  sleep 1
done

# Terminal 2: 배포 실행
git commit --allow-empty -m "test: ALB rolling update"
git push origin main

# Terminal 1에서 200만 출력되는지 확인 (502/503 없음)
```

### 4. WebSocket 연결 테스트 (마인드맵)

```bash
# 브라우저에서 마인드맵 페이지 접속
# https://teammoa.duckdns.org/mindmaps/XXX/

# 브라우저 개발자 도구 → Network → WS 탭
# WebSocket 연결 상태 확인:
# - Status: 101 Switching Protocols
# - Connection: Upgrade
```

### 5. CloudWatch 메트릭 확인

```bash
# ALB 메트릭 확인
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/teammoa-alb/1234567890abcdef \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

---

## 트러블슈팅

### 1. Target Health Check 실패 (unhealthy)

**증상**:
```bash
aws elbv2 describe-target-health --target-group-arn $TARGET_GROUP_ARN
# State: "unhealthy"
# Reason: "Health checks failed with these codes: [502]"
```

**해결 방법**:

```bash
# 1. EC2에서 직접 Health Check 테스트
ssh ubuntu@3.34.102.12
curl http://localhost:8000/health/

# 200 OK 응답 확인
# JSON 응답에서 database, redis 상태 확인

# 2. ALLOWED_HOSTS 확인
cat ~/TeamMoa/TeamMoa/settings/prod.py | grep ALLOWED_HOSTS

# 3. Security Group 확인
aws ec2 describe-security-groups --group-ids $EC2_SG_ID

# 4. 로그 확인
docker logs teammoa_web_prod --tail 50
```

---

### 2. 502 Bad Gateway 에러

**증상**:
```bash
curl https://teammoa.duckdns.org/
# HTTP/1.1 502 Bad Gateway
```

**원인**:
- Target이 unhealthy 상태
- Django 앱이 응답하지 않음
- Security Group에서 ALB → EC2:8000 차단

**해결**:
```bash
# 1. Target Health 확인
aws elbv2 describe-target-health --target-group-arn $TARGET_GROUP_ARN

# 2. Security Group 확인
aws ec2 describe-security-groups --group-ids $EC2_SG_ID \
  | jq '.SecurityGroups[0].IpPermissions'

# 3. EC2 내부에서 8000번 포트 확인
ssh ubuntu@3.34.102.12 "netstat -tuln | grep 8000"

# 4. Django 컨테이너 재시작
ssh ubuntu@3.34.102.12 << 'EOF'
  cd ~/TeamMoa
  docker compose -f docker-compose.prod.yml restart web
  docker compose -f docker-compose.prod.yml ps
EOF
```

---

### 3. WebSocket 연결 끊김

**증상**:
- 마인드맵 실시간 협업 중 연결 끊김
- 브라우저 콘솔: `WebSocket is closed before the connection is established`

**원인**:
- ALB Idle Timeout 기본값 60초
- Sticky Session 미설정

**해결**:
```bash
# 1. ALB Idle Timeout 증가
aws elbv2 modify-load-balancer-attributes \
  --load-balancer-arn $ALB_ARN \
  --attributes Key=idle_timeout.timeout_seconds,Value=3600

# 2. Target Group Stickiness 활성화
aws elbv2 modify-target-group-attributes \
  --target-group-arn $TARGET_GROUP_ARN \
  --attributes Key=stickiness.enabled,Value=true \
               Key=stickiness.type,Value=app_cookie \
               Key=stickiness.app_cookie.cookie_name,Value=sessionid \
               Key=stickiness.app_cookie.duration_seconds,Value=86400

# 3. 확인
aws elbv2 describe-load-balancer-attributes --load-balancer-arn $ALB_ARN
aws elbv2 describe-target-group-attributes --target-group-arn $TARGET_GROUP_ARN
```

---

### 4. CI/CD 배포 실패 (SSH timeout)

**증상**:
```
Error: ssh: connect to host x.x.x.x port 22: Connection timed out
```

**원인**:
- Dynamic Security Group에서 IP 추가 실패
- IAM 권한 부족

**해결**:
```bash
# 1. IAM 권한 확인
aws iam get-user-policy --user-name github-actions --policy-name ec2-access

# 2. Security Group에 수동으로 GitHub Actions IP 추가 (테스트)
GITHUB_IP="20.x.x.x/32"  # GitHub Actions Runner IP
aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr $GITHUB_IP

# 3. 배포 재시도
# GitHub → Actions → Re-run failed jobs
```

---

### 5. Target 등록 후에도 unhealthy

**증상**:
```bash
aws elbv2 describe-target-health --target-group-arn $TARGET_GROUP_ARN
# State: "initial"
# Reason: "Target registration is in progress"

# 5분 후에도 여전히 unhealthy
```

**원인**:
- Health Check Interval/Timeout 설정 문제
- Django 앱 응답 시간 > 5초

**해결**:
```bash
# 1. Target Group Health Check 설정 확인
aws elbv2 describe-target-groups --target-group-arns $TARGET_GROUP_ARN \
  | jq '.TargetGroups[0].HealthCheckIntervalSeconds, .TargetGroups[0].HealthCheckTimeoutSeconds'

# 2. Timeout 증가
aws elbv2 modify-target-group \
  --target-group-arn $TARGET_GROUP_ARN \
  --health-check-timeout-seconds 10

# 3. Django Health Check 엔드포인트 최적화
# (DB 쿼리 캐싱, Redis 응답 시간 개선)
```

---

## 완료 체크리스트

- [ ] VPC 및 Subnet 구성 완료
- [ ] EC2-2 인스턴스 생성 및 설정
- [ ] ALB 생성 및 Target Group 등록
- [ ] ACM SSL 인증서 발급 및 HTTPS 설정
- [ ] Security Group 올바르게 구성
- [ ] Django ALLOWED_HOSTS 및 Health Check 수정
- [ ] CI/CD 파이프라인 Rolling Update 구현
- [ ] Target Group에서 2개 인스턴스 모두 healthy
- [ ] HTTPS 접속 정상 작동
- [ ] WebSocket 연결 안정적
- [ ] 무중단 배포 검증 완료
- [ ] CloudWatch 알람 설정

---

## 참고 자료

- [AWS ALB 공식 문서](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [Target Group Health Check](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html)
- [Rolling Deployment with ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html)
- [ACM 인증서 검증](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html)

---

**작성일**: 2025년 12월 9일
**버전**: 1.0
**문의**: TeamMoa 프로젝트 이슈 페이지
