"""
미인증 계정 자동 삭제 Management Command

3일 이상 인증되지 않은 계정을 자동으로 삭제합니다.
삭제 대상: is_active=False, is_deleted=False, 생성일로부터 3일 경과

사용법:
    python manage.py delete_unverified_users
    python manage.py delete_unverified_users --days 7  # 7일 기준
    python manage.py delete_unverified_users --dry-run  # 실제 삭제 없이 확인만
    python manage.py delete_unverified_users --verbose  # 상세 정보 출력
    python manage.py delete_unverified_users --dry-run --verbose  # 상세 정보 + 삭제 안함
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User


class Command(BaseCommand):
    help = '3일 이상 미인증된 계정을 자동으로 삭제합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='삭제 기준 일수 (기본값: 3일)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 삭제하지 않고 대상만 확인합니다.',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='사용자의 상세 정보를 출력합니다.',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        verbose = options['verbose']

        # 삭제 기준 시점 계산
        cutoff_date = timezone.now() - timedelta(days=days)

        # 삭제 대상 조회 (미인증 + 미삭제 + 기준일 이전 생성)
        unverified_users = User.objects.filter(
            is_active=False,
            is_deleted=False,
            date_joined__lt=cutoff_date
        )

        count = unverified_users.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'삭제 대상 미인증 계정이 없습니다. (기준: {days}일)')
            )
            return

        # 삭제 대상 출력
        self.stdout.write(f'\n삭제 대상 미인증 계정: {count}개')
        self.stdout.write('=' * 80)

        for user in unverified_users:
            days_passed = (timezone.now() - user.date_joined).days

            if verbose:
                # 상세 정보 출력
                self.stdout.write(f'\n[User ID: {user.id}]')
                self.stdout.write(f'  Username      : {user.username}')
                self.stdout.write(f'  Email         : {user.email}')
                self.stdout.write(f'  Nickname      : {user.nickname or "(없음)"}')
                self.stdout.write(f'  Profile       : {user.profile or "(없음)"}')
                self.stdout.write(f'  Date Joined   : {user.date_joined.strftime("%Y-%m-%d %H:%M:%S")}')
                self.stdout.write(f'  Last Login    : {user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else "(없음)"}')
                self.stdout.write(f'  Is Active     : {user.is_active}')
                self.stdout.write(f'  Is Deleted    : {user.is_deleted}')
                self.stdout.write(f'  Deleted At    : {user.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if user.deleted_at else "(없음)"}')
                self.stdout.write(f'  Is Staff      : {user.is_staff}')
                self.stdout.write(f'  Is Superuser  : {user.is_superuser}')
                self.stdout.write(f'  경과 일수      : {days_passed}일')
                self.stdout.write('-' * 80)
            else:
                # 간단한 정보 출력
                self.stdout.write(
                    f'  - ID: {user.id:4d} | Username: {user.username:20s} | '
                    f'Email: {user.email:30s} | {days_passed}일 경과'
                )

        if not verbose:
            self.stdout.write('=' * 80)

        # Dry-run 모드
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY-RUN] 실제로 삭제하지 않았습니다. '
                    f'실제 삭제하려면 --dry-run 옵션을 제거하세요.'
                )
            )
            return

        # 실제 삭제 실행
        deleted_count, _ = unverified_users.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ {deleted_count}개의 미인증 계정을 삭제했습니다.'
            )
        )
