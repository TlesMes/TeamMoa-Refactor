from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.views.generic import TemplateView, ListView, DetailView, DeleteView, FormView
from django.views import View
from django.contrib import messages
from django.urls import reverse

from teams.models import TeamUser, Team
from .forms import CreateMindmapForm
from .models import Comment, Mindmap, Node, NodeConnection
from .services import MindmapService
from accounts.models import User
from common.mixins import TeamMemberRequiredMixin, TeamHostRequiredMixin
import logging


# Create your views here.
class MindmapListPageView(TeamMemberRequiredMixin, ListView):
    model = Mindmap
    template_name = 'mindmaps/mindmap_list_page.html'
    context_object_name = 'mindmaps'
    
    def __init__(self):
        super().__init__()
        self.mindmap_service = MindmapService()
    
    def get_queryset(self):
        return self.mindmap_service.get_team_mindmaps(self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        context['team'] = team
        return context


class MindmapDetailPageView(TeamMemberRequiredMixin, DetailView):
    model = Mindmap
    template_name = 'mindmaps/mindmap_detail_page.html'
    context_object_name = 'mindmap'
    pk_url_kwarg = 'mindmap_id'
    
    def __init__(self):
        super().__init__()
        self.mindmap_service = MindmapService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        
        # 서비스 레이어를 통한 최적화된 조회
        mindmap_data = self.mindmap_service.get_mindmap_with_nodes(self.kwargs['mindmap_id'])
        
        context.update({
            'team': team,
            'nodes': mindmap_data['nodes'],
            'lines': mindmap_data['lines']
        })
        return context


class MindmapCreateView(TeamMemberRequiredMixin, FormView):
    form_class = CreateMindmapForm
    template_name = 'mindmaps/mindmap_create.html'
    
    def __init__(self):
        super().__init__()
        self.mindmap_service = MindmapService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        context['team'] = team
        return context
    
    def form_valid(self, form):
        try:
            mindmap = self.mindmap_service.create_mindmap(
                team_id=self.kwargs['pk'],
                title=form.cleaned_data['title'],
                creator=self.request.user
            )
            messages.success(self.request, f'마인드맵 "{mindmap.title}"가 성공적으로 생성되었습니다.')
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, '마인드맵 생성 중 오류가 발생했습니다.')
            return self.form_invalid(form)
        
        return redirect('mindmaps:mindmap_list_page', pk=self.kwargs['pk'])


class MindmapDeleteView(TeamHostRequiredMixin, View):
    def __init__(self):
        super().__init__()
        self.mindmap_service = MindmapService()
    
    def post(self, request, pk, mindmap_id):
        try:
            mindmap_title = self.mindmap_service.delete_mindmap(mindmap_id, request.user)
            messages.success(request, f'마인드맵 "{mindmap_title}"이 성공적으로 삭제되었습니다.')
        except Exception as e:
            messages.error(request, '마인드맵 삭제 중 오류가 발생했습니다.')
        
        return redirect('mindmaps:mindmap_list_page', pk=pk)


class MindmapCreateNodeView(TeamMemberRequiredMixin, TemplateView):
    def __init__(self):
        super().__init__()
        self.mindmap_service = MindmapService()
    
    def post(self, request, pk, mindmap_id, *args, **kwargs):
        # 요청 데이터 준비
        node_data = {
            'posX': request.POST.get('posX'),
            'posY': request.POST.get('posY'),
            'title': request.POST.get('title'),
            'content': request.POST.get('content'),
            'parent': request.POST.get('parent')
        }
        
        try:
            node, connection_message = self.mindmap_service.create_node(
                mindmap_id=mindmap_id,
                node_data=node_data,
                creator=request.user
            )
            
            success_message = f'노드 "{node.title}"이 성공적으로 생성되었습니다.'
            if connection_message:
                success_message += connection_message
            
            messages.success(request, success_message)
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logging.error(f'노드 생성 오류: {e}')
            messages.error(request, '노드 생성 중 오류가 발생했습니다.')
        
        return redirect('mindmaps:mindmap_detail_page', pk=pk, mindmap_id=mindmap_id)


class MindmapDeleteNodeView(TeamMemberRequiredMixin, View):
    def __init__(self):
        super().__init__()
        self.mindmap_service = MindmapService()
    
    def post(self, request, pk, node_id):
        try:
            node_title, mindmap_id = self.mindmap_service.delete_node(node_id, request.user)
            messages.success(request, f'노드 "{node_title}"이 성공적으로 삭제되었습니다.')
        except Exception as e:
            messages.error(request, '노드 삭제 중 오류가 발생했습니다.')
            # 오류 시 팀 페이지로 리다이렉트
            return redirect('teams:team_detail', pk=pk)
        
        return redirect('mindmaps:mindmap_detail_page', pk=pk, mindmap_id=mindmap_id)


class NodeDetailPageView(TeamMemberRequiredMixin, DetailView):
    model = Node
    template_name = 'mindmaps/node_detail_page.html'
    context_object_name = 'node'
    pk_url_kwarg = 'node_id'
    
    def __init__(self):
        super().__init__()
        self.mindmap_service = MindmapService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        
        # 서비스 레이어를 통한 최적화된 조회
        node_data = self.mindmap_service.get_node_with_comments(self.kwargs['node_id'])
        
        context.update({
            'team': team,
            'comments': node_data['comments']
        })
        return context
    
    def post(self, request, *args, **kwargs):
        node = self.get_object()
        comment_text = request.POST.get("comment")
        
        try:
            self.mindmap_service.create_comment(
                node_id=node.id,
                comment_text=comment_text,
                user=request.user
            )
            messages.success(request, '댓글이 성공적으로 등록되었습니다.')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, '댓글 등록 중 오류가 발생했습니다.')
        
        return redirect('mindmaps:node_detail_page', pk=self.kwargs['pk'], node_id=node.id)


class NodeRecommendView(TeamMemberRequiredMixin, View):
    def __init__(self):
        super().__init__()
        self.mindmap_service = MindmapService()
    
    def post(self, request, pk, node_id, *args, **kwargs):
        try:
            action, recommendation_count = self.mindmap_service.toggle_node_recommendation(
                node_id=node_id,
                user_id=request.user.id
            )
            
            action_text = "추가" if action == "added" else "취소"
            messages.success(request, f'추천이 {action_text}되었습니다. (현재: {recommendation_count}개)')
            
        except Exception as e:
            messages.error(request, '추천 처리 중 오류가 발생했습니다.')
        
        return redirect('mindmaps:node_detail_page', pk=pk, node_id=node_id)


class MindmapEmpowerView(TeamMemberRequiredMixin, View):
    def post(self, request, pk, mindmap_id, user_id, *args, **kwargs):
        # 향후 구현
        messages.info(request, '이 기능은 아직 구현되지 않았습니다.')
        return redirect('mindmaps:mindmap_detail_page', pk=pk, mindmap_id=mindmap_id)


# 하위 호환성을 위한 함수형 뷰 래퍼
mindmap_list_page = MindmapListPageView.as_view()
mindmap_detail_page = MindmapDetailPageView.as_view()
mindmap_create = MindmapCreateView.as_view()
mindmap_delete = MindmapDeleteView.as_view()
mindmap_create_node = MindmapCreateNodeView.as_view()
mindmap_delete_node = MindmapDeleteNodeView.as_view()
mindmap_empower = MindmapEmpowerView.as_view()
node_detail_page = NodeDetailPageView.as_view()
node_vote = NodeRecommendView.as_view()  # 하위 호환성 유지
node_recommend = NodeRecommendView.as_view()  # 새 이름