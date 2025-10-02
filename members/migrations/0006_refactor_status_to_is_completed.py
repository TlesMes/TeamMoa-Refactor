# Generated manually for Todo model refactoring
# Converts status field to is_completed boolean

from django.db import migrations, models


def migrate_status_to_is_completed(apps, schema_editor):
    """
    기존 status 데이터를 is_completed로 변환
    - status='done' → is_completed=True
    - status='in_progress' → is_completed=False (assignee 유지)
    - status='todo' → is_completed=False, assignee=None
    """
    Todo = apps.get_model('members', 'Todo')

    # Done 상태인 TODO들 → is_completed=True
    Todo.objects.filter(status='done').update(is_completed=True)

    # In Progress 상태 → is_completed=False (assignee는 이미 설정되어 있음)
    Todo.objects.filter(status='in_progress').update(is_completed=False)

    # To Do 상태 → is_completed=False, assignee=None
    Todo.objects.filter(status='todo').update(is_completed=False, assignee=None)


def reverse_migrate(apps, schema_editor):
    """
    롤백 시 is_completed를 status로 복원
    - is_completed=True → status='done'
    - is_completed=False, assignee != None → status='in_progress'
    - is_completed=False, assignee == None → status='todo'
    """
    Todo = apps.get_model('members', 'Todo')

    # is_completed=True → status='done'
    Todo.objects.filter(is_completed=True).update(status='done')

    # is_completed=False, assignee 있음 → status='in_progress'
    Todo.objects.filter(is_completed=False, assignee__isnull=False).update(status='in_progress')

    # is_completed=False, assignee 없음 → status='todo'
    Todo.objects.filter(is_completed=False, assignee__isnull=True).update(status='todo')


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0005_alter_todo_assignee'),
    ]

    operations = [
        # 1. is_completed 필드 추가 (기본값 False)
        migrations.AddField(
            model_name='todo',
            name='is_completed',
            field=models.BooleanField(default=False),
        ),

        # 2. 데이터 마이그레이션: status → is_completed
        migrations.RunPython(
            migrate_status_to_is_completed,
            reverse_code=reverse_migrate,
        ),

        # 3. status 필드 제거
        migrations.RemoveField(
            model_name='todo',
            name='status',
        ),
    ]
