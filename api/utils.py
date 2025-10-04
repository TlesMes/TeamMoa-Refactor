"""
API 응답 유틸리티 함수
Django messages를 JSON으로 변환하여 API 응답에 포함
"""
from django.contrib import messages
from rest_framework.response import Response
from rest_framework import status as http_status


def api_response(request, data=None, success=True, status_code=None):
    """
    Django messages를 JSON으로 변환하여 API 응답 생성

    Args:
        request: Django HttpRequest 객체
        data: 응답에 포함할 데이터 (dict)
        success: 성공 여부 (bool, default: True)
        status_code: HTTP 상태 코드 (int, default: 200 또는 400)

    Returns:
        Response: DRF Response 객체

    Example:
        # ViewSet에서 사용
        messages.success(request, '저장되었습니다.')
        return api_response(request, data={'id': 123})

        # 응답 형식
        {
            "success": true,
            "messages": [
                {"message": "저장되었습니다.", "level": "success"}
            ],
            "data": {"id": 123}
        }
    """
    # Django messages 수집
    msg_list = []
    for msg in messages.get_messages(request):
        msg_list.append({
            'message': str(msg.message),
            'level': msg.level_tag  # 'success', 'error', 'warning', 'info', 'debug'
        })

    # 기본 상태 코드 설정
    if status_code is None:
        status_code = http_status.HTTP_200_OK if success else http_status.HTTP_400_BAD_REQUEST

    # 응답 페이로드 구성
    payload = {
        'success': success,
        'messages': msg_list,
    }

    # data가 있으면 추가
    if data is not None:
        if isinstance(data, dict):
            payload.update(data)
        else:
            payload['data'] = data

    return Response(payload, status=status_code)


def api_error_response(request, error_message, status_code=None):
    """
    에러 응답 생성 헬퍼 함수

    Args:
        request: Django HttpRequest 객체
        error_message: 에러 메시지 (str)
        status_code: HTTP 상태 코드 (int, default: 400)

    Returns:
        Response: DRF Response 객체
    """
    messages.error(request, error_message)
    return api_response(
        request,
        success=False,
        status_code=status_code or http_status.HTTP_400_BAD_REQUEST
    )


def api_success_response(request, success_message, data=None, status_code=None):
    """
    성공 응답 생성 헬퍼 함수

    Args:
        request: Django HttpRequest 객체
        success_message: 성공 메시지 (str)
        data: 응답 데이터 (dict or any)
        status_code: HTTP 상태 코드 (int, default: 200)

    Returns:
        Response: DRF Response 객체
    """
    messages.success(request, success_message)
    return api_response(
        request,
        data=data,
        success=True,
        status_code=status_code or http_status.HTTP_200_OK
    )
