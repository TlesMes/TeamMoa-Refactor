from django.db import models

# Create your models here.

class Todo(models.Model):
    content = models.TextField(default="", null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    assignee = models.ForeignKey(
        'teams.TeamUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='todo_set',
        help_text='TODO 담당자 (탈퇴 시 NULL, 미할당 상태로 변경)'
    )
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, default=1)
    milestone = models.ForeignKey(
        'teams.Milestone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='todos',
        help_text='연결된 마일스톤 (마일스톤 삭제 시 NULL, 연결 해제 상태로 변경)'
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.content

    def save(self, *args, **kwargs):
        """
        TODO 저장 시 연결된 마일스톤의 진행률 자동 갱신
        - AUTO 모드 마일스톤만 갱신
        - is_completed, milestone 변경 감지하여 갱신 트리거
        """
        # 기존 객체인지 확인 (생성 vs 수정)
        is_update = self.pk is not None
        old_milestone = None

        # 수정인 경우, is_completed 및 milestone 변경 여부 확인
        if is_update:
            try:
                old_todo = Todo.objects.get(pk=self.pk)
                is_completed_changed = old_todo.is_completed != self.is_completed
                milestone_changed = old_todo.milestone_id != self.milestone_id
                old_milestone = old_todo.milestone
            except Todo.DoesNotExist:
                is_completed_changed = False
                milestone_changed = False
        else:
            is_completed_changed = False
            milestone_changed = False

        # 실제 저장
        super().save(*args, **kwargs)

        # 마일스톤 진행률 갱신 (AUTO 모드만)
        # 1. 새 마일스톤 진행률 갱신 (is_completed 변경 또는 milestone 변경 또는 신규 생성)
        if self.milestone and (is_completed_changed or milestone_changed or not is_update):
            if self.milestone.progress_mode == 'auto':
                self.milestone.update_progress_from_todos()

        # 2. 이전 마일스톤 진행률 갱신 (milestone 변경된 경우)
        if milestone_changed and old_milestone and old_milestone.progress_mode == 'auto':
            old_milestone.update_progress_from_todos()

    def detach_from_milestone(self):
        """마일스톤 연결 해제 및 진행률 갱신"""
        if not self.milestone:
            return

        old_milestone = self.milestone
        self.milestone = None
        self.save()

        # 이전 마일스톤 진행률 갱신 (AUTO 모드만)
        if old_milestone.progress_mode == 'auto':
            old_milestone.update_progress_from_todos()