import re
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    기본 사용자 정보 조회용 Serializer
    민감한 정보(비밀번호, 이메일, 권한 등)는 제외
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'date_joined']
        read_only_fields = ['id', 'username', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    본인 프로필 조회용 Serializer
    자신의 정보에 한해 이메일 등 추가 정보 포함
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'email', 'profile', 'date_joined', 'last_login']
        read_only_fields = ['id', 'username', 'date_joined', 'last_login']


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    프로필 수정용 Serializer
    수정 가능한 필드만 제한적으로 허용
    """
    class Meta:
        model = User
        fields = ['nickname', 'profile']

    def validate_nickname(self, value):
        """닉네임 중복 검사 (길이 검사는 모델 validators에서 처리)"""
        # 중복 검사 (자신 제외)
        user = self.instance
        if user and User.objects.filter(nickname=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('이미 사용 중인 닉네임입니다.')

        return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    회원가입용 Serializer
    완전한 유효성 검사 및 중복 검사 포함
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'nickname', 'password', 'password_confirm', 'profile']
        extra_kwargs = {
            'password': {'write_only': True},
            'profile': {'required': False, 'allow_blank': True}
        }

    def validate_username(self, value):
        """사용자명 중복 검사 (길이/형식 검사는 모델 validators에서 처리)"""
        # 중복 검사만 수행 (unique=True가 모델에 있지만 더 명확한 에러 메시지 제공)
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('이미 사용중인 사용자 ID입니다.')

        return value

    def validate_email(self, value):
        """이메일 유효성 및 중복 검사"""
        # 형식 검사
        REGEX_EMAIL = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.fullmatch(REGEX_EMAIL, value):
            raise serializers.ValidationError('이메일 형식이 맞지 않습니다.')

        # 중복 검사
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('이미 사용중인 이메일입니다.')

        return value

    def validate_nickname(self, value):
        """닉네임 유효성 및 중복 검사"""
        # 길이 검사
        if len(value) < 2:
            raise serializers.ValidationError('닉네임은 2자 이상이어야 합니다.')
        if len(value) > 10:
            raise serializers.ValidationError('닉네임은 10자 이하여야 합니다.')

        # 중복 검사
        if User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError('이미 사용중인 닉네임입니다.')

        return value

    def validate_profile(self, value):
        """프로필 메시지 유효성 검사"""
        if value and len(value) > 500:
            raise serializers.ValidationError('프로필 메시지는 500자 이하여야 합니다.')
        return value

    def validate(self, data):
        """전체 데이터 검증"""
        # 비밀번호 확인
        password = data.get('password')
        password_confirm = data.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': '비밀번호가 일치하지 않습니다.'
            })

        # Django 기본 비밀번호 검증
        if password:
            try:
                # 임시 사용자 객체 생성하여 비밀번호 검증
                temp_user = User(
                    username=data.get('username', ''),
                    email=data.get('email', ''),
                    nickname=data.get('nickname', '')
                )
                validate_password(password, temp_user)
            except DjangoValidationError as error:
                # Django 검증 에러를 한글로 변환
                korean_messages = []
                for message in error.messages:
                    if 'password is too short' in message or 'must contain at least' in message:
                        korean_messages.append('비밀번호는 최소 8자 이상이어야 합니다.')
                    elif 'password is too common' in message or 'common password' in message:
                        korean_messages.append('너무 일반적인 비밀번호입니다.')
                    elif 'password is entirely numeric' in message or 'entirely numeric' in message:
                        korean_messages.append('비밀번호가 모두 숫자로만 구성되어 있습니다.')
                    elif 'similar to the' in message or 'too similar' in message:
                        korean_messages.append('비밀번호가 개인 정보와 너무 유사합니다.')
                    else:
                        korean_messages.append(str(message))

                raise serializers.ValidationError({
                    'password': korean_messages
                })

        return data

    def create(self, validated_data):
        """사용자 생성"""
        # password_confirm 제거 (DB 저장용 필드가 아님)
        validated_data.pop('password_confirm', None)

        # 비밀번호 암호화하여 사용자 생성
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False  # 이메일 인증 전까지 비활성화
        user.save()

        return user


class PasswordChangeSerializer(serializers.Serializer):
    """
    비밀번호 변경용 Serializer
    """
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        """현재 비밀번호 확인"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('현재 비밀번호가 올바르지 않습니다.')
        return value

    def validate(self, data):
        """전체 데이터 검증"""
        new_password = data.get('new_password')
        new_password_confirm = data.get('new_password_confirm')

        # 새 비밀번호 확인
        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': '새 비밀번호가 일치하지 않습니다.'
            })

        # Django 기본 비밀번호 검증
        user = self.context['request'].user
        try:
            validate_password(new_password, user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({
                'new_password': error.messages
            })

        return data

    def save(self):
        """비밀번호 변경 실행"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    로그인용 Serializer
    """
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """사용자 인증 검증"""
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError('아이디와 비밀번호를 모두 입력해주세요.')

        # 사용자 인증
        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError('아이디 또는 비밀번호가 올바르지 않습니다.')

        if not user.is_active:
            raise serializers.ValidationError('계정이 비활성화되어 있습니다. 이메일 인증을 확인해주세요.')

        data['user'] = user
        return data


class UserAvailabilitySerializer(serializers.Serializer):
    """
    실시간 중복 검사용 Serializer
    """
    field = serializers.ChoiceField(choices=['username', 'email', 'nickname'])
    value = serializers.CharField(max_length=255)

    def validate(self, data):
        """중복 검사 실행"""
        field = data['field']
        value = data['value']

        # 필드별 존재 여부 검사
        if field == 'username':
            exists = User.objects.filter(username=value).exists()
        elif field == 'email':
            exists = User.objects.filter(email=value).exists()
        elif field == 'nickname':
            exists = User.objects.filter(nickname=value).exists()
        else:
            raise serializers.ValidationError('유효하지 않은 필드입니다.')

        data['available'] = not exists
        return data