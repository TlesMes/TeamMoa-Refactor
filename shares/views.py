from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.views import View
from .models import Post
from .forms import PostWriteForm
from .services import ShareService
from accounts.models import User
from django.contrib import messages

import urllib
import os
from django.http import HttpResponse, Http404
import mimetypes
import logging
from teams.models import Team, TeamUser
from common.mixins import TeamMemberRequiredMixin
from django.core.exceptions import PermissionDenied

# URL 패턴 상수
LOGIN_PAGE = 'accounts:login'
POST_LIST_PAGE = 'shares:post_list'
POST_DETAIL_PAGE = 'shares:post_detail'
MAIN_PAGE = 'teams:main_page'


# PostAuthorRequiredMixin은 서비스 레이어로 이동되었습니다.
# ShareService.check_post_author() 메서드를 사용하세요.


class PostListView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'shares/post_list.html'
    
    def __init__(self):
        super().__init__()
        self.share_service = ShareService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team_id = self.kwargs['pk']
        
        # 페이지 번호 가져오기
        page = self.request.GET.get('page', 1)
        
        # 서비스 레이어를 통한 게시글 조회
        posts_data = self.share_service.get_team_posts(team_id, page=page, per_page=10)
        
        context.update({
            'post_list': posts_data['posts'],
            'page_obj': posts_data['posts'],  # 템플릿 호환성을 위해
            'team': posts_data['team'],
            'team_id': team_id
        })
        return context

class PostDetailView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'shares/post_detail.html'
    
    def __init__(self):
        super().__init__()
        self.share_service = ShareService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=kwargs['pk'])
        
        # 서비스 레이어를 통한 게시글 조회
        post_data = self.share_service.get_post_detail(
            post_id=kwargs['post_id'],
            user=self.request.user
        )
        
        context.update({
            'post': post_data['post'],
            'post_auth': post_data['is_author'],
            'team': team
        })
        return context


post_detail_view = PostDetailView.as_view()

class PostWriteView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'shares/post_write_renew.html'
    
    def __init__(self):
        super().__init__()
        self.share_service = ShareService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        context.update({
            'form': PostWriteForm(),
            'pk': self.kwargs['pk'],
            'team': team
        })
        return context
    
    def post(self, request, pk):
        form = PostWriteForm(request.POST, request.FILES)
        team = get_object_or_404(Team, pk=pk)
        
        if form.is_valid():
            try:
                # 폼 데이터 준비
                post_data = {
                    'title': form.cleaned_data['title'],
                    'article': form.cleaned_data['article']
                }
                
                # 서비스 레이어를 통한 게시글 생성
                post = self.share_service.create_post(
                    team_id=pk,
                    post_data=post_data,
                    files_data=request.FILES,
                    writer=request.user
                )
                
                messages.success(request, '성공적으로 등록되었습니다.')
                return redirect(POST_LIST_PAGE, pk)
                
            except ValueError as e:
                messages.error(request, str(e))
                return render(request, self.template_name, {
                    'form': form, 
                    'pk': pk, 
                    'team': team
                })
            except Exception as e:
                messages.error(request, '게시글 등록 중 오류가 발생했습니다.')
                return render(request, self.template_name, {
                    'form': form, 
                    'pk': pk, 
                    'team': team
                })
        
        return render(request, self.template_name, {
            'form': form, 
            'pk': pk, 
            'team': team
        })


post_write_view = PostWriteView.as_view()


class PostEditView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'shares/post_write_renew.html'
    
    def __init__(self):
        super().__init__()
        self.share_service = ShareService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=kwargs['pk'])
        post = get_object_or_404(Post, id=kwargs['post_id'])
        
        # 권한 검증
        if not self.share_service.check_post_author(kwargs['post_id'], self.request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied('본인 게시글이 아닙니다.')
        
        context.update({
            'form': PostWriteForm(instance=post),
            'edit': '수정하기',
            'team': team
        })
        return context
    
    def post(self, request, pk, post_id):
        team = get_object_or_404(Team, pk=pk)
        
        try:
            # 권한 검증은 서비스에서 처리됨
            post_data = {
                'title': request.POST.get('title'),
                'article': request.POST.get('article')
            }
            
            post = self.share_service.update_post(
                post_id=post_id,
                post_data=post_data,
                user=request.user
            )
            
            messages.success(request, "수정되었습니다.")
            return redirect(POST_LIST_PAGE, pk)
            
        except ValueError as e:
            messages.error(request, str(e))
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect(POST_LIST_PAGE, pk)
        except Exception as e:
            messages.error(request, '게시글 수정 중 오류가 발생했습니다.')
        
        # 오류 시 폼 다시 표시
        post = get_object_or_404(Post, id=post_id)
        form = PostWriteForm(request.POST, instance=post)
        return render(request, self.template_name, {
            'form': form,
            'edit': '수정하기',
            'team': team
        })


post_edit_view = PostEditView.as_view()

class PostDeleteView(TeamMemberRequiredMixin, View):
    def __init__(self):
        super().__init__()
        self.share_service = ShareService()
    
    def post(self, request, pk, post_id):
        try:
            post_title = self.share_service.delete_post(post_id, request.user)
            messages.success(request, f'게시글 "{post_title}"이 삭제되었습니다.')
        except PermissionDenied as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, '게시글 삭제 중 오류가 발생했습니다.')
        
        return redirect(POST_LIST_PAGE, pk)


post_delete_view = PostDeleteView.as_view()


class PostDownloadView(TeamMemberRequiredMixin, TemplateView):
    def __init__(self):
        super().__init__()
        self.share_service = ShareService()
    
    def get(self, request, pk, post_id, *args, **kwargs):
        try:
            # 서비스 레이어를 통한 파일 다운로드 처리
            response = self.share_service.handle_file_download(post_id, request.user)
            return response
            
        except ValueError as e:
            messages.error(request, str(e))
            # 게시글이 존재하는 경우 상세 페이지로, 없으면 메인으로
            try:
                post = get_object_or_404(Post, pk=post_id)
                return redirect(POST_DETAIL_PAGE, pk=post.isTeams_id, post_id=post_id)
            except:
                return redirect(MAIN_PAGE)
                
        except Exception as e:
            logging.error(f'파일 다운로드 오류: {e}')
            messages.error(request, '파일 다운로드 중 오류가 발생했습니다.')
            try:
                post = get_object_or_404(Post, pk=post_id)
                return redirect(POST_DETAIL_PAGE, pk=post.isTeams_id, post_id=post_id)
            except:
                return redirect(MAIN_PAGE)


post_download_view = PostDownloadView.as_view()
