from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class TeamMoaPageNumberPagination(PageNumberPagination):
    """
    TeamMoa API 표준 페이지네이션 클래스
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """
        TeamMoa 표준 페이지네이션 응답 형식
        """
        return Response({
            'pagination': {
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'page_size': self.get_page_size(self.request),
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
                'next_page': self.page.next_page_number() if self.page.has_next() else None,
                'previous_page': self.page.previous_page_number() if self.page.has_previous() else None,
            },
            'results': data
        })


class SmallResultsSetPagination(PageNumberPagination):
    """
    작은 데이터셋용 페이지네이션 (댓글, 알림 등)
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class LargeResultsSetPagination(PageNumberPagination):
    """
    큰 데이터셋용 페이지네이션 (로그, 히스토리 등)
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200