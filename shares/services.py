import os
import urllib.parse
import mimetypes
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.conf import settings

from .models import Post
from teams.models import Team, TeamUser
from accounts.models import User


class ShareService:
    """
    게시판(Shares) 관련 비즈니스 로직을 처리하는 서비스 클래스
    
    주요 책임:
    - 게시글 CRUD 및 권한 관리
    - 파일 업로드/다운로드 처리
    - 팀 기반 게시글 필터링
    - 페이지네이션 처리
    """
    
    # ================================
    # 게시글 CRUD 메서드
    # ================================
    
    @transaction.atomic
    def create_post(self, team_id, post_data, files_data, user):
        """
        새로운 게시글을 생성합니다.

        Args:
            team_id (int): 팀 ID
            post_data (dict): {'title': str, 'article': str}
            files_data (dict): 업로드 파일 정보
            user (User): 작성자

        Returns:
            Post: 생성된 게시글 객체

        Raises:
            ValueError: 필수 필드가 누락되거나 유효하지 않은 경우
            ValidationError: 팀이 존재하지 않거나 사용자가 팀 멤버가 아닌 경우
        """
        # 필수 필드 검증
        if not post_data.get('title') or not post_data.get('title').strip():
            raise ValueError('제목을 입력해주세요.')

        if not post_data.get('article') or not post_data.get('article').strip():
            raise ValueError('내용을 입력해주세요.')

        # TeamUser 조회 (팀 멤버 검증)
        teamuser = get_object_or_404(TeamUser, team_id=team_id, user=user)

        # 게시글 생성
        post = Post.objects.create(
            title=post_data['title'].strip(),
            article=post_data['article'].strip(),
            team_id=team_id,  # 팀 직접 지정
            teamuser=teamuser  # 작성자 정보
        )

        # 파일 업로드 처리
        if files_data and 'upload_files' in files_data:
            upload_file = files_data['upload_files']
            post.upload_files = upload_file
            post.filename = upload_file.name
            post.save()

        return post
    
    def update_post(self, post_id, post_data, user):
        """
        게시글을 수정합니다.
        
        Args:
            post_id (int): 게시글 ID
            post_data (dict): 수정할 데이터
            user (User): 수정을 요청한 사용자
            
        Returns:
            Post: 수정된 게시글 객체
            
        Raises:
            ValueError: 필수 필드가 누락되거나 유효하지 않은 경우
            PermissionDenied: 권한이 없는 경우
        """
        post = get_object_or_404(Post, pk=post_id)
        
        # 권한 검증 (작성자 본인 또는 관리자)
        if not self.check_post_author(post_id, user):
            raise PermissionDenied('본인 게시글이 아닙니다.')
        
        # 필수 필드 검증
        if not post_data.get('title') or not post_data.get('title').strip():
            raise ValueError('제목을 입력해주세요.')
        
        if not post_data.get('article') or not post_data.get('article').strip():
            raise ValueError('내용을 입력해주세요.')
        
        # 게시글 수정
        post.title = post_data['title'].strip()
        post.article = post_data['article'].strip()
        post.save()
        
        return post
    
    def delete_post(self, post_id, user):
        """
        게시글을 삭제합니다 (파일도 함께 삭제).
        
        Args:
            post_id (int): 게시글 ID
            user (User): 삭제를 요청한 사용자
            
        Returns:
            str: 삭제된 게시글 제목
            
        Raises:
            PermissionDenied: 권한이 없는 경우
        """
        post = get_object_or_404(Post, pk=post_id)
        
        # 권한 검증
        if not self.check_post_author(post_id, user):
            raise PermissionDenied('본인 게시글이 아닙니다.')
        
        post_title = post.title
        
        # 파일 정리 후 게시글 삭제 (모델의 delete 메서드가 파일 정리 처리)
        post.delete()
        
        return post_title
    
    def get_team_posts(self, team_id, page=1, per_page=10):
        """
        팀의 게시글 목록을 페이지네이션과 함께 조회합니다.

        Args:
            team_id (int): 팀 ID
            page (int): 페이지 번호 (기본값: 1)
            per_page (int): 페이지당 항목 수 (기본값: 10)

        Returns:
            dict: {
                'posts': Page 객체 (페이지네이션된 게시글),
                'team': Team 객체
            }
        """
        team = get_object_or_404(Team, pk=team_id)

        # 최적화된 쿼리: 팀 필터 + 작성자 정보 사전 로딩
        # team FK를 직접 사용하여 teamuser=None인 게시물도 조회 가능
        posts_queryset = Post.objects.filter(team=team).select_related('teamuser__user').order_by('-id')

        # 페이지네이션 적용
        paginator = Paginator(posts_queryset, per_page)
        posts_page = paginator.get_page(page)

        return {
            'posts': posts_page,
            'team': team
        }

    def search_posts(self, team_id, query, search_type='all', page=1, per_page=10):
        """
        팀의 게시글을 검색합니다.

        Args:
            team_id (int): 팀 ID
            query (str): 검색어
            search_type (str): 검색 타입 ('all', 'title_content', 'title', 'content', 'writer')
            page (int): 페이지 번호 (기본값: 1)
            per_page (int): 페이지당 항목 수 (기본값: 10)

        Returns:
            dict: {
                'posts': Page 객체 (페이지네이션된 검색 결과),
                'team': Team 객체
            }
        """
        team = get_object_or_404(Team, pk=team_id)

        # 검색어가 없으면 빈 결과 반환
        if not query or not query.strip():
            return {
                'posts': Paginator([], per_page).get_page(page),
                'team': team
            }

        query = query.strip()

        # 기본 쿼리셋: 팀 필터 + 작성자 정보 사전 로딩
        # team FK를 직접 사용하여 teamuser=None인 게시물도 검색 가능
        posts_queryset = Post.objects.filter(team=team).select_related('teamuser__user')

        # 검색 타입별 필터링
        if search_type == 'title':
            # 제목만 검색
            posts_queryset = posts_queryset.filter(title__icontains=query)
        elif search_type == 'content':
            # 내용만 검색
            posts_queryset = posts_queryset.filter(article__icontains=query)
        elif search_type == 'writer':
            # 작성자 닉네임 검색
            posts_queryset = posts_queryset.filter(teamuser__user__nickname__icontains=query)
        elif search_type == 'title_content':
            # 제목 또는 내용 검색
            posts_queryset = posts_queryset.filter(
                Q(title__icontains=query) | Q(article__icontains=query)
            )
        else:  # 'all'
            # 제목, 내용, 작성자 모두 검색
            posts_queryset = posts_queryset.filter(
                Q(title__icontains=query) |
                Q(article__icontains=query) |
                Q(teamuser__user__nickname__icontains=query)
            )

        # 정렬: 최신순
        posts_queryset = posts_queryset.order_by('-id')

        # 페이지네이션 적용
        paginator = Paginator(posts_queryset, per_page)
        posts_page = paginator.get_page(page)

        return {
            'posts': posts_page,
            'team': team
        }
    
    # ================================
    # 게시글 조회 메서드
    # ================================
    
    def get_post_detail(self, post_id, user):
        """
        게시글 상세 정보를 조회합니다.

        Args:
            post_id (int): 게시글 ID
            user (User): 조회하는 사용자

        Returns:
            dict: {
                'post': Post 객체,
                'is_author': bool (작성자 여부)
            }
        """
        post = get_object_or_404(Post.objects.select_related('teamuser__user'), pk=post_id)

        return {
            'post': post,
            'is_author': bool(post.teamuser and post.teamuser.user == user)
        }
    
    def check_post_author(self, post_id, user):
        """
        사용자가 게시글의 작성자인지 또는 관리자인지 확인합니다.

        Args:
            post_id (int): 게시글 ID
            user (User): 확인할 사용자

        Returns:
            bool: 작성자이거나 관리자인 경우 True
        """
        post = get_object_or_404(Post.objects.select_related('teamuser__user'), pk=post_id)

        # 작성자 본인이거나 관리자 권한 확인
        return (post.teamuser and post.teamuser.user == user) or user.is_superuser
    
    # ================================
    # 파일 관리 메서드
    # ================================
    
    def handle_file_download(self, post_id, user):
        """
        게시글의 첨부파일 다운로드를 처리합니다.
        
        Args:
            post_id (int): 게시글 ID
            user (User): 다운로드 요청 사용자
            
        Returns:
            HttpResponse: 파일 다운로드 응답 또는 None (오류시)
            
        Raises:
            ValueError: 파일이 없거나 접근할 수 없는 경우
        """
        post = get_object_or_404(Post, pk=post_id)
        
        # 업로드 파일이 없는 경우
        if not post.upload_files:
            raise ValueError('다운로드할 파일이 없습니다.')
        
        # 파일 경로 처리
        try:
            url = post.upload_files.url[1:]  # 맨 앞의 '/' 제거
            file_url = urllib.parse.unquote(url)
            
            # 파일 존재 여부 확인
            if not os.path.exists(file_url):
                raise ValueError('서버에서 파일을 찾을 수 없습니다.')
            
            # 파일 읽기 및 응답 생성
            with open(file_url, 'rb') as fh:
                quote_file_url = urllib.parse.quote(post.filename.encode('utf-8'))
                response = HttpResponse(
                    fh.read(), 
                    content_type=mimetypes.guess_type(file_url)[0]
                )
                response['Content-Disposition'] = f'attachment;filename*=UTF-8\'\'{quote_file_url}'
                return response
                
        except Exception as e:
            raise ValueError(f'파일 다운로드 중 오류가 발생했습니다: {str(e)}')
    
    def cleanup_post_files(self, post):
        """
        게시글 삭제 시 관련 파일들을 정리합니다.
        (현재는 Post 모델의 delete 메서드에서 처리하고 있음)
        
        Args:
            post (Post): 삭제할 게시글 객체
            
        Note:
            이 메서드는 향후 파일 정리 로직을 확장할 때 사용
        """
        if post.upload_files:
            try:
                file_path = os.path.join(settings.MEDIA_ROOT, post.upload_files.path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                # 파일 삭제 실패해도 DB 레코드는 삭제되도록 처리
                import logging
                logging.warning(f'파일 삭제 실패: {e}')
    
    # ================================
    # 유틸리티 메서드
    # ================================
    
    def get_post_with_team_check(self, post_id, team_id):
        """
        게시글이 특정 팀에 속하는지 확인하며 조회합니다.

        Args:
            post_id (int): 게시글 ID
            team_id (int): 팀 ID

        Returns:
            Post: 게시글 객체

        Raises:
            ValidationError: 게시글이 해당 팀에 속하지 않는 경우
        """
        post = get_object_or_404(Post.objects.select_related('team'), pk=post_id)

        # team FK로 직접 확인 (teamuser와 무관하게 팀 검증 가능)
        if post.team_id != team_id:
            raise ValidationError('해당 팀의 게시글이 아닙니다.')

        return post