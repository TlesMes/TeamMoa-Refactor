"""
로컬 부하 테스트 전용 설정 (2026-09-10 한계점 탐색 실험용)

prod.py를 그대로 상속하되, **평문 HTTP로 접근하기 위한 최소한의 항목만** 끈다.
DEBUG=False, WhiteNoise, CONN_MAX_AGE, 로깅 등 성능에 영향을 주는 설정은
prod와 동일하게 유지한다. (dev.py는 DEBUG=True + debug_toolbar라
쿼리 로그가 메모리에 누적되어 부하 측정에 쓸 수 없다.)

prod 대비 차이점은 아래 3줄이 전부이며, 리포트에 명시한다.
"""
from .prod import *  # noqa: F401,F403

# HTTPS 종단(ALB/Nginx)이 없는 로컬 평문 HTTP 환경이므로 아래만 해제한다.
# 이걸 켜두면 모든 요청이 301로 리다이렉트되고 세션 쿠키가 내려가지 않아
# 로그인 자체가 불가능하다. 성능 특성과는 무관한 항목이다.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DRF 속도 제한 해제 (부하 테스트 한정)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# base.py의 전역 throttle은 anon 100/hour, user 1000/hour다.
#  - 로그인 API는 AllowAny(익명)이므로 AnonRateThrottle이 **IP 단위**로 걸린다.
#    부하는 노트북 1대(단일 IP)에서 나오므로 시간당 100회 로그인 후 전부 429가 된다.
#  - 인증 후 API 요청도 사용자당 1000/hour라 VU당 1~2 RPS면 수 분 내에 소진된다.
# 이 상태로 재면 "서버가 언제 무너지는가"가 아니라 "DRF 카운터가 언제 차는가"를
# 재게 된다. 한계점 탐색이 목적이므로 해제하고, 해제했다는 사실을 리포트에 명시한다.
# (prod에서는 이 정책이 인프라 한계보다 먼저 걸린다는 것 자체가 하나의 결과다.)
REST_FRAMEWORK = {**REST_FRAMEWORK}  # noqa: F405
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}
