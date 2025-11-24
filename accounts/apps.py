from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """앱 시작 시 Site 도메인 자동 업데이트"""
        from django.conf import settings
        from django.contrib.sites.models import Site

        try:
            site = Site.objects.get(id=settings.SITE_ID)
            if site.domain != settings.SITE_DOMAIN or site.name != settings.SITE_NAME:
                site.domain = settings.SITE_DOMAIN
                site.name = settings.SITE_NAME
                site.save()
        except Site.DoesNotExist:
            # Site가 없으면 생성
            Site.objects.create(
                id=settings.SITE_ID,
                domain=settings.SITE_DOMAIN,
                name=settings.SITE_NAME
            )
        except Exception:
            # 마이그레이션 중이거나 DB가 준비되지 않은 경우 무시
            pass
