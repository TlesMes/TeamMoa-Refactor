"""
accounts 앱의 시그널 핸들러

마이그레이션 완료 후 자동으로 Site 도메인을 업데이트합니다.
"""
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def update_site_domain(sender, **_kwargs):
    """마이그레이션 완료 후 Site 도메인 업데이트

    accounts 앱 마이그레이션 시에만 실행되며,
    SITE_ID에 해당하는 Site 객체의 도메인과 이름을 업데이트합니다.

    Args:
        sender: 마이그레이션을 실행한 앱 설정
        **_kwargs: 추가 키워드 인자 (사용하지 않음)
    """
    if sender.name == 'accounts':  # accounts 앱 마이그레이션 시에만
        try:
            Site.objects.update_or_create(
                id=settings.SITE_ID,
                defaults={
                    'domain': settings.SITE_DOMAIN,
                    'name': settings.SITE_NAME
                }
            )
        except Exception:
            pass  # 마이그레이션 중 실패 무시
