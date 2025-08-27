from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.views import View
from .models import Post
from .forms import PostWriteForm
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
POST_DETAIL_PAGE = 'shares:post_detail_view'
MAIN_PAGE = 'teams:main_page'


class PostAuthorRequiredMixin:
    """게시글 작성자 또는 관리자만 접근 가능한 Mixin"""
    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs.get('post_id'))
        if post.writer != request.user and request.user.level != '0':
            messages.error(request, "본인 게시글이 아닙니다.")
            return redirect(POST_LIST_PAGE, kwargs.get('pk'))
        return super().dispatch(request, *args, **kwargs)


class PostListView(TeamMemberRequiredMixin, ListView):
    model = Post
    paginate_by = 10
    template_name = 'shares/post_list.html'
    context_object_name = 'post_list'
    
    def get_team(self):
        if not hasattr(self, '_team'):
            self._team = get_object_or_404(Team, pk=self.kwargs["pk"])
        return self._team
    
    def get_queryset(self):
        team = self.get_team()
        return Post.objects.filter(isTeams=team.id).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_team()
        context.update({
            'team': team,
            'team_id': team.id
        })
        return context

class PostDetailView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'shares/post_detail1.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=kwargs['pk'])
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        
        # 작성자 본인인가를 템플릿에 전달
        post_auth = self.request.user == post.writer
        
        context.update({
            'post': post,
            'post_auth': post_auth,
            'team': team
        })
        return context


post_detail_view = PostDetailView.as_view()

class PostWriteView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'shares/post_write_renew.html'
    
    def get_team(self):
        if not hasattr(self, '_team'):
            self._team = get_object_or_404(Team, pk=self.kwargs['pk'])
        return self._team
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form': PostWriteForm(),
            'pk': self.kwargs['pk'],
            'team': self.get_team()
        })
        return context
    
    def post(self, request, pk):
        form = PostWriteForm(request.POST, request.FILES)
        team = self.get_team()
        
        if form.is_valid():
            post = form.save(commit=False)
            post.writer = request.user
            post.isTeams_id = pk
            
            if request.FILES and 'upload_files' in request.FILES:
                post.filename = request.FILES['upload_files'].name
            
            post.save()
            messages.success(request, '성공적으로 등록되었습니다.')
            return redirect(POST_LIST_PAGE, pk)
        
        return render(request, self.template_name, {
            'form': form, 
            'pk': pk, 
            'team': team
        })


post_write_view = PostWriteView.as_view()


class PostEditView(PostAuthorRequiredMixin, TeamMemberRequiredMixin, TemplateView):
    template_name = 'shares/post_write_renew.html'
    
    def get_objects(self):
        if not hasattr(self, '_objects'):
            self._objects = {
                'post': get_object_or_404(Post, id=self.kwargs['post_id']),
                'team': get_object_or_404(Team, pk=self.kwargs['pk'])
            }
        return self._objects
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        objects = self.get_objects()
        context.update({
            'form': PostWriteForm(instance=objects['post']),
            'edit': '수정하기',
            'team': objects['team']
        })
        return context
    
    def post(self, request, pk, post_id):
        objects = self.get_objects()
        form = PostWriteForm(request.POST, instance=objects['post'])
        
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, "수정되었습니다.")
            return redirect(POST_LIST_PAGE, pk)
        
        return render(request, self.template_name, {
            'form': form,
            'edit': '수정하기',
            'team': objects['team']
        })


post_edit_view = PostEditView.as_view()

class PostDeleteView(PostAuthorRequiredMixin, TeamMemberRequiredMixin, View):
    def post(self, request, pk, post_id):
        team = get_object_or_404(Team, pk=pk)
        post = get_object_or_404(Post, id=post_id)
        
        post_title = post.title
        post.delete()
        
        messages.success(request, f'게시글 "{post_title}"이 삭제되었습니다.')
        return redirect(POST_LIST_PAGE, pk)


post_delete_view = PostDeleteView.as_view()


class PostDownloadView(TeamMemberRequiredMixin, TemplateView):
    def get(self, request, post_id, *args, **kwargs):
        try:
            post = get_object_or_404(Post, pk=post_id)
        except Http404:
            messages.error(request, '파일이 존재하지 않습니다.')
            return redirect(MAIN_PAGE)
        
        # 업로드 파일이 없는 경우
        if not post.upload_files:
            messages.error(request, '다운로드할 파일이 없습니다.')
            return redirect(POST_DETAIL_PAGE, pk=post.isTeams_id, post_id=post_id)
        
        try:
            url = post.upload_files.url[1:]
            file_url = urllib.parse.unquote(url)
            
            if os.path.exists(file_url):
                with open(file_url, 'rb') as fh:
                    quote_file_url = urllib.parse.quote(post.filename.encode('utf-8'))
                    response = HttpResponse(fh.read(), content_type=mimetypes.guess_type(file_url)[0])
                    response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'%s' % quote_file_url
                    return response
            else:
                messages.error(request, '서버에서 파일을 찾을 수 없습니다.')
                return redirect(POST_DETAIL_PAGE, pk=post.isTeams_id, post_id=post_id)
                
        except Exception as e:
            logging.error(f'파일 다운로드 오류: {e}')
            messages.error(request, '파일 다운로드 중 오류가 발생했습니다.')
            return redirect(POST_DETAIL_PAGE, pk=post.isTeams_id, post_id=post_id)


post_download_view = PostDownloadView.as_view()
