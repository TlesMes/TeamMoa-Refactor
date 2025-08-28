from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.views import View
from django.http import JsonResponse
from django.db.models import Count, Q, Prefetch
from members.forms import CreateTodoForm
from members.models import Todo
from teams.models import Team, TeamUser
from django.contrib import messages
from common.mixins import TeamMemberRequiredMixin
from django.utils import timezone
import json

# URL 패턴 상수
TEAM_MEMBERS_PAGE = 'members:team_members_page'


class TeamMembersPageView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'members/team_members_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=kwargs['pk'])
        
        # 🚀 최적화: 단일 쿼리로 모든 멤버 데이터 + 통계 조회
        members_with_stats = TeamUser.objects.filter(team=team).annotate(
            todo_count=Count('todo_set', filter=Q(todo_set__team=team)),
            completed_count=Count('todo_set', 
                filter=Q(todo_set__team=team, todo_set__status='done')),
            in_progress_count=Count('todo_set',
                filter=Q(todo_set__team=team, todo_set__status='in_progress'))
        ).select_related('user').prefetch_related(
            Prefetch('todo_set', 
                queryset=Todo.objects.filter(team=team).order_by('created_at'))
        )
        
        # 미할당 할일만 별도 조회 (효율성을 위해)
        todos_unassigned = Todo.objects.filter(team=team, assignee__isnull=True)
        form = CreateTodoForm()
        
        # 현재 사용자가 팀장인지 확인
        is_host = team.host == self.request.user
        
        # 🎯 최적화된 데이터 구조 - 이미 prefetch된 데이터 활용
        members_data = []
        for member in members_with_stats:
            members_data.append({
                'member': member,
                'todos': member.todo_set.all(),  # prefetch된 데이터 사용
                'todo_count': member.todo_count,  # annotate된 값 사용
                'completed_count': member.completed_count,  # annotate된 값 사용
                'in_progress_count': member.in_progress_count,  # 추가 통계
            })
        
        context.update({
            'team': team,
            'members': members_with_stats,  # 최적화된 쿼리셋
            'todos_unassigned': todos_unassigned,
            'members_data': members_data,  # 최적화된 구조화된 데이터
            'form': form,
            'is_host': is_host
        })
        return context
    
    def post(self, request, pk):
        form = CreateTodoForm(request.POST)
        if form.is_valid():
            self.member_add_todo(request, pk, form.cleaned_data['content'])
        return redirect(TEAM_MEMBERS_PAGE, pk=pk)
    
    def member_add_todo(self, request, pk, content):
        user = request.user
        team = get_object_or_404(Team, pk=pk)
        todo = Todo()
        todo.content = content
        todo.team = team
        todo.status = 'todo'
        todo.save()


team_members_page = TeamMembersPageView.as_view()

class MemberCompleteTodoView(TeamMemberRequiredMixin, View):
    def post(self, request, pk, todo_id):
        team = get_object_or_404(Team, pk=pk)
        todo = get_object_or_404(Todo, pk=todo_id)
        
        if todo.status == 'done':
            todo.status = 'todo'
            todo.assignee = None
            todo.completed_at = None
        else:
            todo.status = 'done'
            todo.completed_at = timezone.now()
        todo.save()
        
        status = "완료" if todo.status == 'done' else "미완료"
        messages.success(request, f'할 일 상태가 "{status}"로 변경되었습니다.')
        return redirect(TEAM_MEMBERS_PAGE, pk=pk)


class MemberDeleteTodoView(TeamMemberRequiredMixin, View):
    def post(self, request, pk, todo_id):
        team = get_object_or_404(Team, pk=pk)
        todo = get_object_or_404(Todo, pk=todo_id)
        
        todo.delete()
        
        messages.success(request, f'할 일이 삭제되었습니다.')
        return redirect(TEAM_MEMBERS_PAGE, pk=pk)


member_complete_Todo = MemberCompleteTodoView.as_view()
member_delete_Todo = MemberDeleteTodoView.as_view()




# Ajax API 뷰들
class MoveTodoView(TeamMemberRequiredMixin, View):
    """드래그&드롭으로 할일 상태 변경"""
    
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            todo_id = data.get('todo_id')
            new_status = data.get('new_status')
            new_order = data.get('new_order', 0)
            
            team = get_object_or_404(Team, pk=pk)
            current_teamuser = TeamUser.objects.select_related('user').get(
                team=team, user=request.user
            )
            todo = get_object_or_404(Todo, pk=todo_id, team=team)
            
            # 권한 체크
            if not self._can_move_todo(todo, request.user, team):
                return JsonResponse({'success': False, 'error': '권한이 없습니다.'})
            
            # 상태 변경
            old_status = todo.status
            todo.status = new_status
            todo.order = new_order
            
            # 할당자 처리
            if new_status == 'in_progress' and not todo.assignee:
                todo.assignee = current_teamuser
            elif new_status == 'todo':
                todo.assignee = None
                todo.completed_at = None
            elif new_status == 'done':
                todo.completed_at = timezone.now()
            
            todo.save()
            
            return JsonResponse({
                'success': True,
                'message': f'할 일이 {self._get_status_display(new_status)}(으)로 이동되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    def _can_move_todo(self, todo, user, team):
        """할일 이동 권한 체크"""
        # 팀장은 모든 할일 조작 가능
        if team.host == user:
            return True
        
        # 자신에게 할당된 할일만 조작 가능
        current_teamuser = self.get_current_teamuser(team, user)
        if todo.assignee == current_teamuser or todo.assignee is None:
            return True
        
        return False
    
    def _get_status_display(self, status):
        status_map = {
            'todo': 'To Do',
            'in_progress': 'In Progress', 
            'done': 'Done'
        }
        return status_map.get(status, status)


move_todo = MoveTodoView.as_view()


# 새로운 Ajax API 뷰들
class AssignTodoView(TeamMemberRequiredMixin, View):
    """드래그&드롭으로 할일을 팀원에게 할당"""
    
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            todo_id = data.get('todo_id')
            member_id = data.get('member_id')
            
            team = get_object_or_404(Team, pk=pk)
            is_host = team.host == request.user
            
            todo = get_object_or_404(Todo, pk=todo_id, team=team)
            member = get_object_or_404(TeamUser, pk=member_id, team=team)
            
            # 권한 체크: 팀장이거나 미할당 할일만
            if not (is_host or todo.assignee is None):
                messages.error(request, '권한이 없습니다.')
                return JsonResponse({'success': False})
            
            # 권한 체크: 팀장이 아닌데, 다른 팀원에게 작업 할당
            if not (is_host or member.user == request.user):
                messages.error(request, '권한이 없습니다.')
                return JsonResponse({'success': False})

            # 할당 처리
            todo.assignee = member
            todo.status = 'in_progress'
            todo.save()
            
            messages.success(request, f'{todo.content}이(가) {member.user.nickname}님에게 할당되었습니다.')
            
            return JsonResponse({
                'success': True
            })
            
        except Exception as e:
            messages.error(request, '할일 할당 중 오류가 발생했습니다.')
            return JsonResponse({'success': False})


class CompleteTodoView(TeamMemberRequiredMixin, View):
    """체크박스로 할일 완료/미완료 토글"""
    
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            todo_id = data.get('todo_id')
            
            team = get_object_or_404(Team, pk=pk)
            current_teamuser = TeamUser.objects.select_related('user').get(
                team=team, user=request.user
            )
            is_host = team.host == request.user
            
            todo = get_object_or_404(Todo, pk=todo_id, team=team)
            
            # 권한 체크: 팀장이거나 자신에게 할당된 할일
            if not (is_host or todo.assignee == current_teamuser):
                messages.error(request, '권한이 없습니다.')
                return JsonResponse({'success': False})
            
            # 완료 상태 토글
            if todo.status == 'done':
                todo.status = 'in_progress'
                todo.completed_at = None
                messages.success(request, '미완료로 변경되었습니다.')
            else:
                todo.status = 'done'
                todo.completed_at = timezone.now()
                messages.success(request, '완료되었습니다.')
            
            todo.save()
            
            return JsonResponse({
                'success': True,
                'new_status': todo.status
            })
            
        except Exception as e:
            messages.error(request, '할일 완료 처리 중 오류가 발생했습니다.')
            return JsonResponse({'success': False})


class ReturnToBoardView(TeamMemberRequiredMixin, View):
    """할일을 다시 Todo 보드로 되돌리기"""
    
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            todo_id = data.get('todo_id')
            
            team = get_object_or_404(Team, pk=pk)
            current_teamuser = TeamUser.objects.select_related('user').get(
                team=team, user=request.user
            )
            is_host = team.host == request.user
            
            todo = get_object_or_404(Todo, pk=todo_id, team=team)
            
            # 권한 체크: 팀장이거나 자신에게 할당된 할일
            if not (is_host or todo.assignee == current_teamuser):
                messages.error(request, '권한이 없습니다.')
                return JsonResponse({'success': False})
            
            # 할당 해제 및 상태 초기화
            todo.assignee = None
            todo.status = 'todo'
            todo.completed_at = None
            todo.save()
            
            messages.success(request, '할일이 보드로 되돌려졌습니다.')
            
            return JsonResponse({
                'success': True
            })
            
        except Exception as e:
            messages.error(request, '할일 되돌리기 중 오류가 발생했습니다.')
            return JsonResponse({'success': False})


assign_todo = AssignTodoView.as_view()
complete_todo = CompleteTodoView.as_view()
return_to_board = ReturnToBoardView.as_view()