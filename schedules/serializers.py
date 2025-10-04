from rest_framework import serializers
from .models import PersonalDaySchedule
from teams.models import TeamUser


class PersonalDayScheduleSerializer(serializers.ModelSerializer):
    """개인 일별 스케줄 직렬화"""
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = PersonalDaySchedule
        fields = ['id', 'date', 'owner_id', 'owner_name', 'available_hours']
        read_only_fields = ['id', 'owner_id', 'owner_name']

    def get_owner_name(self, obj):
        """소유자 이름 반환"""
        return obj.owner.user.nickname or obj.owner.user.username


class ScheduleCreateSerializer(serializers.Serializer):
    """주간 스케줄 생성/업데이트용 직렬화"""
    week_start = serializers.DateField(help_text="주간 시작 날짜 (월요일)")
    schedule_data = serializers.JSONField(help_text="시간대별 체크박스 데이터 {time_0-1: true, ...}")

    def validate_schedule_data(self, value):
        """스케줄 데이터 검증"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('스케줄 데이터는 객체 형태여야 합니다.')
        return value


class TeamAvailabilitySerializer(serializers.Serializer):
    """팀 가용성 조회 결과 직렬화"""
    date = serializers.DateField()
    availability = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="시간대별 가능한 인원 수 {0: 3, 9: 5, ...}"
    )


class TeamScheduleQuerySerializer(serializers.Serializer):
    """팀 스케줄 조회 파라미터 직렬화"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, data):
        """시작일과 종료일 검증"""
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError('시작일은 종료일보다 이전이어야 합니다.')
        return data
