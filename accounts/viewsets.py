from django.db import transaction
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import auth
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .models import User
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    UserRegistrationSerializer,
    PasswordChangeSerializer,
    UserAvailabilitySerializer,
    UserLoginSerializer
)
from .services import AuthService


class RegistrationRateThrottle(AnonRateThrottle):
    """회원가입 API에 대한 속도 제한"""
    scope = 'registration'
    rate = '5/hour'  # 시간당 5회 제한


class AvailabilityRateThrottle(AnonRateThrottle):
    """중복 검사 API에 대한 속도 제한"""
    scope = 'availability'
    rate = '30/min'  # 분당 30회 제한


class UserViewSet(viewsets.GenericViewSet):
    """
    사용자 관련 API ViewSet

    보안을 위해 ModelViewSet의 기본 CRUD를 비활성화하고
    필요한 액션만 선택적으로 구현
    """

    def get_queryset(self):
        """현재 사용자만 접근 가능하도록 쿼리셋 제한"""
        if self.request.user.is_authenticated:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.none()

    def get_object(self):
        """객체 조회 시 현재 사용자만 반환"""
        if self.action in ['me', 'update_profile', 'change_password']:
            return self.request.user
        return super().get_object()

    def get_permissions(self):
        """액션별 권한 설정"""
        if self.action in ['register', 'check_availability', 'login']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_throttles(self):
        """액션별 속도 제한 설정"""
        if self.action == 'register':
            return [RegistrationRateThrottle()]
        elif self.action == 'check_availability':
            return [AvailabilityRateThrottle()]
        return super().get_throttles()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        현재 로그인한 사용자의 프로필 정보 조회

        GET /api/v1/users/me/
        """
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        현재 사용자의 프로필 정보 수정

        PUT/PATCH /api/v1/users/update_profile/

        수정 가능한 필드: nickname, profile
        """
        user = request.user
        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=request.method == 'PATCH'
        )

        if serializer.is_valid():
            serializer.save()
            # 업데이트된 정보를 프로필 시리얼라이저로 반환
            response_serializer = UserProfileSerializer(user)
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def register(self, request):
        """
        새 사용자 회원가입

        POST /api/v1/users/register/

        필수 필드: username, email, nickname, password, password_confirm
        선택 필드: profile
        """
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            try:
                # 사용자 생성 (이메일 인증 전까지 비활성화 상태)
                user = serializer.save()

                # 이메일 인증 메일 발송
                auth_service = AuthService()
                auth_service.send_activation_email(user, get_current_site(request))

                # 생성된 사용자 정보 반환 (민감정보 제외)
                response_serializer = UserSerializer(user)
                return Response({
                    'user': response_serializer.data,
                    'message': '회원가입이 완료되었습니다. 이메일을 확인하여 계정을 활성화해주세요.'
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                # 이메일 발송 실패 등의 경우 롤백
                return Response({
                    'error': '회원가입 중 오류가 발생했습니다.',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        사용자 로그인

        POST /api/v1/users/login/

        필수 필드: username, password
        """
        serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Django 세션 로그인
            auth.login(request, user)

            # 로그인된 사용자 정보 반환
            response_serializer = UserProfileSerializer(user)
            return Response({
                'user': response_serializer.data,
                'message': '로그인되었습니다.'
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        사용자 로그아웃

        POST /api/v1/users/logout/

        인증된 사용자만 접근 가능
        """
        # Django 세션 로그아웃
        auth.logout(request)

        return Response({
            'message': '로그아웃되었습니다.'
        })

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        현재 사용자의 비밀번호 변경

        POST /api/v1/users/change_password/

        필수 필드: current_password, new_password, new_password_confirm
        """
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': '비밀번호가 성공적으로 변경되었습니다.'
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def check_availability(self, request):
        """
        사용자명, 이메일, 닉네임의 사용 가능 여부 실시간 확인

        POST /api/v1/users/check_availability/

        필수 필드: field ('username', 'email', 'nickname'), value

        응답: {'field': '필드명', 'value': '검사값', 'available': true/false}
        """
        serializer = UserAvailabilitySerializer(data=request.data)

        if serializer.is_valid():
            return Response({
                'field': serializer.validated_data['field'],
                'value': serializer.validated_data['value'],
                'available': serializer.validated_data['available']
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def profile_stats(self, request):
        """
        현재 사용자의 활동 통계 정보

        GET /api/v1/users/profile_stats/
        """
        user = request.user

        # 사용자가 속한 팀 수 계산
        from teams.models import TeamUser
        team_count = TeamUser.objects.filter(user=user).count()

        # 기타 통계 정보 수집
        stats = {
            'user_id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'joined_teams_count': team_count,
            'account_created': user.date_joined,
            'last_login': user.last_login,
            'is_active': user.is_active
        }

        return Response(stats)

    # 기본 ModelViewSet의 위험한 메서드들을 명시적으로 비활성화
    def list(self, request, *args, **kwargs):
        """사용자 목록 조회 - 보안상 비활성화"""
        return Response(
            {'error': '사용자 목록 조회는 지원하지 않습니다.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def create(self, request, *args, **kwargs):
        """사용자 생성 - register 액션 사용 필요"""
        return Response(
            {'error': '/api/v1/users/register/ 엔드포인트를 사용해주세요.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def retrieve(self, request, *args, **kwargs):
        """특정 사용자 조회 - me 액션 사용 필요"""
        return Response(
            {'error': '/api/v1/users/me/ 엔드포인트를 사용해주세요.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def update(self, request, *args, **kwargs):
        """사용자 정보 수정 - update_profile 액션 사용 필요"""
        return Response(
            {'error': '/api/v1/users/update_profile/ 엔드포인트를 사용해주세요.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def destroy(self, request, *args, **kwargs):
        """사용자 삭제 - 보안상 비활성화"""
        return Response(
            {'error': '계정 삭제는 관리자에게 문의해주세요.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )