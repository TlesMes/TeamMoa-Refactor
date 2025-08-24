from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.views.generic import TemplateView, ListView, DetailView, DeleteView, FormView
from django.views import View
from django.contrib import messages
from django.urls import reverse

from teams.models import TeamUser, Team
from .forms import CreateMindmapForm
from .models import Comment, Mindmap, Node, NodeConnection, NodeUser
from accounts.models import User
from common.mixins import TeamMemberRequiredMixin, TeamHostRequiredMixin
import logging


# Create your views here.
class MindmapListPageView(TeamMemberRequiredMixin, ListView):
    model = Mindmap
    template_name = 'mindmaps/mindmap_list_page.html'
    context_object_name = 'mindmaps'
    
    def get_queryset(self):
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        return Mindmap.objects.filter(team=team).order_by('-id')
    
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        mindmap = self.get_object()
        nodes = Node.objects.filter(mindmap=mindmap).order_by('id')
        lines = NodeConnection.objects.filter(mindmap=mindmap).order_by('id')
        
        context.update({
            'team': team,
            'nodes': nodes,
            'lines': lines
        })
        return context


class MindmapCreateView(TeamMemberRequiredMixin, FormView):
    form_class = CreateMindmapForm
    template_name = 'mindmaps/mindmap_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        context['team'] = team
        return context
    
    def form_valid(self, form):
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        mindmap = Mindmap.objects.create(
            title=form.cleaned_data['title'],
            team=team
        )
        messages.success(self.request, f'마인드맵 "{mindmap.title}"가 성공적으로 생성되었습니다.')
        return redirect('mindmaps:mindmap_list_page', pk=self.kwargs['pk'])


class MindmapDeleteView(TeamHostRequiredMixin, DeleteView):
    model = Mindmap
    pk_url_kwarg = 'mindmap_id'
    
    def get_success_url(self):
        messages.success(self.request, '마인드맵이 성공적으로 삭제되었습니다.')
        return reverse('mindmaps:mindmap_list_page', kwargs={'pk': self.kwargs['pk']})


class MindmapCreateNodeView(TeamMemberRequiredMixin, TemplateView):
    def post(self, request, pk, mindmap_id, *args, **kwargs):
        team = get_object_or_404(Team, pk=pk)
        mindmap = get_object_or_404(Mindmap, pk=mindmap_id)
        
        # 필수 필드 검증
        required_fields = ['posX', 'posY', 'title', 'content']
        for field in required_fields:
            if not request.POST.get(field):
                messages.error(request, f'{field} 필드는 필수입니다.')
                return redirect('mindmaps:mindmap_detail_page', pk=pk, mindmap_id=mindmap_id)
        
        try:
            # 노드 생성
            node = Node.objects.create(
                posX=int(request.POST["posX"]),
                posY=int(request.POST["posY"]),
                title=request.POST["title"],
                content=request.POST["content"],
                mindmap=mindmap
            )
            
            # 팀 멤버를 노드에 자동 추가
            members = TeamUser.objects.filter(team=team)
            for member in members:
                node.user.add(member.user)
            
            # 부모 노드 연결 (선택사항)
            parent_title = request.POST.get("parent")
            if parent_title:
                try:
                    parent_node = Node.objects.get(title=parent_title, mindmap=mindmap)
                    NodeConnection.objects.create(from_node=node, to_node=parent_node, mindmap=mindmap)
                except Node.DoesNotExist:
                    messages.warning(request, '부모 노드를 찾을 수 없어 연결이 생성되지 않았습니다.')
            
            messages.success(request, f'노드 "{node.title}"이 성공적으로 생성되었습니다.')
            
        except (ValueError, TypeError) as e:
            messages.error(request, '잘못된 입력값입니다. 위치 정보는 숫자여야 합니다.')
        except Exception as e:
            logging.error(f'노드 생성 오류: {e}')
            messages.error(request, '노드 생성 중 오류가 발생했습니다.')
        
        return redirect('mindmaps:mindmap_detail_page', pk=pk, mindmap_id=mindmap_id)


class MindmapDeleteNodeView(TeamMemberRequiredMixin, DeleteView):
    model = Node
    pk_url_kwarg = 'node_id'
    
    def get_success_url(self):
        node = self.get_object()
        messages.success(self.request, f'노드 "{node.title}"이 성공적으로 삭제되었습니다.')
        return reverse('mindmaps:mindmap_detail_page', kwargs={
            'pk': self.kwargs['pk'], 
            'mindmap_id': node.mindmap.id
        })


class NodeDetailPageView(TeamMemberRequiredMixin, DetailView):
    model = Node
    template_name = 'mindmaps/node_detail_page.html'
    context_object_name = 'node'
    pk_url_kwarg = 'node_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        node = self.get_object()
        comments = Comment.objects.filter(node=node).order_by('-id')
        
        context.update({
            'team': team,
            'comments': comments
        })
        return context
    
    def post(self, request, *args, **kwargs):
        node = self.get_object()
        comment_text = request.POST.get("comment")
        
        if not comment_text or not comment_text.strip():
            messages.error(request, '댓글 내용을 입력해주세요.')
        else:
            Comment.objects.create(
                comment=comment_text.strip(),
                node=node,
                user=request.user
            )
            messages.success(request, '댓글이 성공적으로 등록되었습니다.')
        
        return redirect('mindmaps:node_detail_page', pk=self.kwargs['pk'], node_id=node.id)


class NodeVoteView(TeamMemberRequiredMixin, View):
    def post(self, request, pk, node_id, *args, **kwargs):
        node = get_object_or_404(Node, pk=node_id)
        
        try:
            # 기존 투표 확인
            nodeuser = NodeUser.objects.get(node=node, user=request.user)
            
            # 투표 상태 토글
            if nodeuser.vote:
                nodeuser.vote = False
                vote_action = "취소"
            else:
                nodeuser.vote = True  
                vote_action = "추가"
            nodeuser.save()
            
        except NodeUser.DoesNotExist:
            # 투표 기록이 없으면 새로 생성 (투표)
            NodeUser.objects.create(node=node, user=request.user, vote=True)
            vote_action = "추가"
            
        except NodeUser.MultipleObjectsReturned:
            # 중복 데이터 처리
            nodeuser = NodeUser.objects.filter(node=node, user=request.user).first()
            NodeUser.objects.filter(node=node, user=request.user).exclude(pk=nodeuser.pk).delete()
            logging.warning(f'NodeUser 중복 제거: node_id={node_id}, user_id={request.user.id}')
            
            # 투표 상태 토글
            nodeuser.vote = not nodeuser.vote
            nodeuser.save()
            vote_action = "추가" if nodeuser.vote else "취소"
        
        # 현재 득표수 계산
        current_votes = NodeUser.objects.filter(node=node, vote=True).count()
        
        messages.success(request, f'투표가 {vote_action}되었습니다. (현재: {current_votes}표)')
        return redirect('mindmaps:node_detail_page', pk=pk, node_id=node_id)


class MindmapEmpowerView(TeamMemberRequiredMixin, View):
    def post(self, request, pk, mindmap_id, user_id, *args, **kwargs):
        # 구현되지 않은 기능으로 보임 - 향후 구현
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
node_vote = NodeVoteView.as_view()