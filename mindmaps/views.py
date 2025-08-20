from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.core.paginator import Paginator

from teams.models import TeamUser
from .forms import CreateMindmapForm
from teams.models import Team
from .models import Comment, Mindmap, Node, NodeConnection, NodeUser
from accounts.models import User
import logging
def is_member(request, pk) -> bool:
    user = request.user
    if not user.is_authenticated:
        return redirect('/accounts/login')

    if user.is_authenticated:
        team = get_object_or_404(Team, pk=pk)
        if user in team.members.all():
            return True
        else:
            return False

# Create your views here.
def mindmap_list_page(request, pk):
    if not is_member(request, pk):
        return HttpResponse('<script>alert("팀원이 아닙니다.")</script>''<script>location.href="/teams/"</script>')

    user = request.user
    team = get_object_or_404(Team, pk=pk)
    mindmaps = Mindmap.objects.filter(team=team)
  
    return render(request, 'mindmaps/mindmap_list_page.html', {'mindmaps':mindmaps, 'team':team})

def mindmap_detail_page(request, pk, mindmap_id):
    if not is_member(request, pk):
        return HttpResponse('<script>alert("팀원이 아닙니다.")</script>''<script>location.href="/teams/"</script>')
    
    user = request.user
    team = get_object_or_404(Team, pk=pk)
    mindmap = Mindmap.objects.get(pk=mindmap_id)
    nodes = Node.objects.filter(mindmap=mindmap)
    lines = NodeConnection.objects.filter(mindmap=mindmap)
    return render(request, 'mindmaps/mindmap_detail_page.html',{'nodes':nodes,'team':team,'mindmap':mindmap, 'lines':lines})
    

def mindmap_create(request, pk):
    user = request.user
    team = get_object_or_404(Team, pk=pk)
    if request.method =='POST':
        form = CreateMindmapForm(request.POST)
        if form.is_valid():
            mindmap = Mindmap()
            mindmap.title = form.cleaned_data['title']
            mindmap.team = team
            mindmap.save()
            return redirect(f'/mindmaps/mindmap_list_page/{pk}')
    else:
        form = CreateMindmapForm()
    return render(request, 'mindmaps/mindmap_create.html',{'form':form, 'team':team})

def mindmap_delete(request, pk, mindmap_id):
    team = get_object_or_404(Team, pk=pk)
    mindmap = get_object_or_404(Mindmap, pk=mindmap_id)
    
    # 팀장만 마인드맵을 삭제할 수 있음
    if request.user == team.host:
        mindmap.delete()
        return redirect('mindmaps:mindmap_list_page', pk=pk)
    else:
        return HttpResponse('<script>alert("팀장만 마인드맵을 삭제할 수 있습니다.")</script><script>history.back()</script>')

def mindmap_create_node(request, pk, mindmap_id):
    team = get_object_or_404(Team, pk=pk)
    mindmap=Mindmap.objects.get(pk=mindmap_id)
    if request.method =='POST':
        node = Node()
        node.posX = request.POST["posX"]
        node.posY = request.POST["posY"]
        node.title = request.POST["title"]
        node.content = request.POST["content"]
        node.mindmap = mindmap
        node.save()
        members=TeamUser.objects.filter(team=team)
        for member in members:
            node.user.add(member.user)
        parent=request.POST["parent"]
        if parent != "":
            parentnode = Node.objects.get(title=parent,mindmap=mindmap)
            NodeConnection.objects.create(from_node=node,to_node=parentnode,mindmap=mindmap)

    return redirect(f'/mindmaps/mindmap_detail_page/{pk}/{mindmap_id}')


def mindmap_delete_node(request, pk, node_id):
    team = get_object_or_404(Team, pk=pk)
    node = Node.objects.get(pk=node_id)
    node.delete()
    return redirect(f'/mindmaps/mindmap_detail_page/{pk}/{node.mindmap.id}')

def mindmap_empower(request, pk, mindmap_id, user_id):
    pass

def node_detail_page(request, pk, node_id):
    team = get_object_or_404(Team, pk=pk)
    node = Node.objects.get(pk=node_id)
    if request.method =='POST':
        user = request.user
        comment = Comment()
        comment.comment = request.POST["comment"]
        comment.node = node
        comment.user = user
        comment.save()
    comments = Comment.objects.filter(node=node)
    return render(request, 'mindmaps/node_detail_page.html',{'node':node, 'team':team,'comments':comments})
    
def node_vote(request, pk, node_id):
    user = request.user
    team = get_object_or_404(Team, pk=pk)
    node = Node.objects.get(pk=node_id)
    
    # 중복 NodeUser 처리를 위한 안전한 조회
    try:
        nodeuser = NodeUser.objects.get(node=node, user=user)
    except NodeUser.MultipleObjectsReturned:
        # 중복이 있으면 첫 번째 것을 사용하고 나머지는 삭제
        nodeuser = NodeUser.objects.filter(node=node, user=user).first()
        NodeUser.objects.filter(node=node, user=user).exclude(pk=nodeuser.pk).delete()
    except NodeUser.DoesNotExist:
        # NodeUser가 없으면 생성
        nodeuser = NodeUser.objects.create(node=node, user=user, voted=False)
    
    comments = Comment.objects.filter(node=node)
    if nodeuser.voted:
        node.vote = node.vote - 1
    else:
        node.vote = node.vote + 1
    node.save()
    nodeuser.voted = not nodeuser.voted
    nodeuser.save()

    return render(request, 'mindmaps/node_detail_page.html',{'node':node, 'team':team,'comments':comments})


def node_add_comment(request):
    pass

