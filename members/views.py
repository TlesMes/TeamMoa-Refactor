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
from .services import TodoService
import json

# URL 패턴 상수
TEAM_MEMBERS_PAGE = 'members:team_members_page'


class TeamMembersPageView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'members/team_members_page.html'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.todo_service = TodoService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=kwargs['pk'])
        
        # 서비스에서 최적화된 데이터 조회
        todo_data = self.todo_service.get_team_todos_with_stats(team)
        form = CreateTodoForm()
        
        # 현재 사용자가 팀장인지 확인
        is_host = team.host == self.request.user
        
        context.update({
            'team': team,
            'members': todo_data['members'],
            'todos_unassigned': todo_data['todos_unassigned'],
            'todos_done': todo_data['todos_done'],
            'members_data': todo_data['members_data'],
            'form': form,
            'is_host': is_host
        })
        return context
    
    def post(self, request, pk):
        form = CreateTodoForm(request.POST)
        if form.is_valid():
            try:
                team = get_object_or_404(Team, pk=pk)
                self.todo_service.create_todo(
                    team=team,
                    content=form.cleaned_data['content'],
                    creator=request.user
                )
                messages.success(request, '할 일이 성공적으로 추가되었습니다.')
            except ValueError as e:
                messages.error(request, str(e))
        return redirect(TEAM_MEMBERS_PAGE, pk=pk)


team_members_page = TeamMembersPageView.as_view()

class MemberCompleteTodoView(TeamMemberRequiredMixin, View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.todo_service = TodoService()
        
    def post(self, request, pk, todo_id):
        try:
            team = get_object_or_404(Team, pk=pk)
            todo, new_status = self.todo_service.complete_todo(todo_id, team, request.user)
            
            status_display = "완료" if new_status == 'done' else "미완료"
            messages.success(request, f'할 일 상태가 "{status_display}"로 변경되었습니다.')
            
        except ValueError as e:
            messages.error(request, str(e))
            
        return redirect(TEAM_MEMBERS_PAGE, pk=pk)


class MemberDeleteTodoView(TeamMemberRequiredMixin, View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.todo_service = TodoService()
        
    def post(self, request, pk, todo_id):
        try:
            team = get_object_or_404(Team, pk=pk)
            todo_content = self.todo_service.delete_todo(todo_id, team)
            messages.success(request, f'"{todo_content}" 할 일이 삭제되었습니다.')
            
        except Exception as e:
            messages.error(request, '할 일 삭제 중 오류가 발생했습니다.')
            
        return redirect(TEAM_MEMBERS_PAGE, pk=pk)


member_complete_Todo = MemberCompleteTodoView.as_view()
member_delete_Todo = MemberDeleteTodoView.as_view()




# Ajax API 뷰들
class MoveTodoView(TeamMemberRequiredMixin, View):
    """드래그&드롭으로 할일 상태 변경"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.todo_service = TodoService()
    
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            todo_id = data.get('todo_id')
            new_status = data.get('new_status')
            new_order = data.get('new_order', 0)
            
            team = get_object_or_404(Team, pk=pk)
            
            todo = self.todo_service.move_todo(
                todo_id=todo_id,
                new_status=new_status,
                team=team,
                requester=request.user,
                new_order=new_order
            )
            
            status_display = self.todo_service.get_status_display(new_status)
            
            return JsonResponse({
                'success': True,
                'message': f'할 일이 {status_display}(으)로 이동되었습니다.'
            })
            
        except ValueError as e:
            return JsonResponse({'success': False, 'error': str(e)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': '서버 오류가 발생했습니다.'})


move_todo = MoveTodoView.as_view()


# 새로운 Ajax API 뷰들
class AssignTodoView(TeamMemberRequiredMixin, View):
    """드래그&드롭으로 할일을 팀원에게 할당"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.todo_service = TodoService()
    
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            todo_id = data.get('todo_id')
            member_id = data.get('member_id')
            
            team = get_object_or_404(Team, pk=pk)
            
            todo = self.todo_service.assign_todo(
                todo_id=todo_id,
                assignee_id=member_id, 
                team=team,
                requester=request.user
            )
            
            assignee_name = todo.assignee.user.nickname or todo.assignee.user.username
            messages.success(request, f'{todo.content}이(가) {assignee_name}님에게 할당되었습니다.')
            
            return JsonResponse({'success': True})
            
        except ValueError as e:
            messages.error(request, str(e))
            return JsonResponse({'success': False})
        except Exception as e:
            messages.error(request, '할일 할당 중 오류가 발생했습니다.')
            return JsonResponse({'success': False})


class CompleteTodoView(TeamMemberRequiredMixin, View):
    """체크박스로 할일 완료/미완료 토글"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.todo_service = TodoService()
    
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            todo_id = data.get('todo_id')
            
            team = get_object_or_404(Team, pk=pk)
            
            todo, new_status = self.todo_service.complete_todo(todo_id, team, request.user)
            
            status_message = '완료되었습니다.' if new_status == 'done' else '미완료로 변경되었습니다.'
            messages.success(request, status_message)
            
            return JsonResponse({
                'success': True,
                'new_status': new_status
            })
            
        except ValueError as e:
            messages.error(request, str(e))
            return JsonResponse({'success': False})
        except Exception as e:
            messages.error(request, '할일 완료 처리 중 오류가 발생했습니다.')
            return JsonResponse({'success': False})


class ReturnToBoardView(TeamMemberRequiredMixin, View):
    """할일을 다시 Todo 보드로 되돌리기"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.todo_service = TodoService()
    
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            todo_id = data.get('todo_id')
            
            team = get_object_or_404(Team, pk=pk)
            
            self.todo_service.return_to_board(todo_id, team, request.user)
            
            messages.success(request, '할일이 보드로 되돌려졌습니다.')
            
            return JsonResponse({'success': True})
            
        except ValueError as e:
            messages.error(request, str(e))
            return JsonResponse({'success': False})
        except Exception as e:
            messages.error(request, '할일 되돌리기 중 오류가 발생했습니다.')
            return JsonResponse({'success': False})


assign_todo = AssignTodoView.as_view()
complete_todo = CompleteTodoView.as_view()
return_to_board = ReturnToBoardView.as_view()