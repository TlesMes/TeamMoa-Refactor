#!/bin/bash

# root 권한에서 실행해야 함
# Docker PID 1 환경변수를 export 형식으로 변환
tr '\0' '\n' < /proc/1/environ | awk -F= 'NF==2 {print "export \""$1"="$2"\""}' > /tmp/container_env.sh

# 환경변수 로드
source /tmp/container_env.sh

# cleanup
rm -f /tmp/container_env.sh

cd /app
/opt/venv/bin/python manage.py delete_unverified_users --verbose
