from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    TeamMoa API의 공통 예외 처리기
    DRF 기본 예외 처리를 확장하여 일관된 에러 응답 형식 제공
    """
    # DRF 기본 예외 처리 먼저 실행
    response = exception_handler(exc, context)

    if response is not None:
        # 기본 에러 응답 형식을 TeamMoa 표준으로 변경
        custom_response_data = {
            'error': True,
            'message': '요청 처리 중 오류가 발생했습니다.',
            'details': response.data,
            'status_code': response.status_code
        }

        # 에러 타입별 맞춤 메시지
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['message'] = '잘못된 요청입니다.'
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['message'] = '로그인이 필요합니다.'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['message'] = '접근 권한이 없습니다.'
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data['message'] = '요청한 리소스를 찾을 수 없습니다.'
        elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            custom_response_data['message'] = '허용되지 않은 요청 방법입니다.'
        elif response.status_code >= 500:
            custom_response_data['message'] = '서버 내부 오류가 발생했습니다.'
            # 서버 에러는 로그에 기록
            logger.error(f"Server error: {exc}", exc_info=True)

        response.data = custom_response_data

    else:
        # DRF에서 처리되지 않은 예외들 (Django의 일반 예외들)
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        response = Response(
            {
                'error': True,
                'message': '예상치 못한 오류가 발생했습니다.',
                'details': str(exc),
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response


class TeamMoaAPIException(Exception):
    """
    TeamMoa API 전용 커스텀 예외 클래스
    """
    default_message = "API 오류가 발생했습니다."
    default_status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message=None, status_code=None, details=None):
        self.message = message or self.default_message
        self.status_code = status_code or self.default_status_code
        self.details = details or {}
        super().__init__(self.message)


class TeamNotFound(TeamMoaAPIException):
    """팀을 찾을 수 없을 때 발생하는 예외"""
    default_message = "팀을 찾을 수 없습니다."
    default_status_code = status.HTTP_404_NOT_FOUND


class TeamPermissionDenied(TeamMoaAPIException):
    """팀 접근 권한이 없을 때 발생하는 예외"""
    default_message = "팀에 대한 접근 권한이 없습니다."
    default_status_code = status.HTTP_403_FORBIDDEN


class InvalidTeamOperation(TeamMoaAPIException):
    """잘못된 팀 작업을 시도할 때 발생하는 예외"""
    default_message = "유효하지 않은 팀 작업입니다."
    default_status_code = status.HTTP_400_BAD_REQUEST