from django.shortcuts import render
from django.views.generic import ListView
from .models import Post
from django.shortcuts import render,redirect,get_object_or_404
from .forms import PostWriteForm
from accounts.models import User
from django.contrib import messages

import urllib
import os
from django.http import HttpResponse, Http404
import mimetypes
import logging
from teams.models import Team, Team_User

#로그인 확인 임포트
#404 임포트
class PostListView(ListView):
    model = Post
    paginate_by = 10
    template_name = 'shares/post_list.html'
    context_object_name = 'post_list'
   # print("PostList id",Post.isTeams)
    def get_queryset(self):
        team = Post.objects.get(pk=self.kwargs["pk"])
        Post.isTeams = team.id
        post_list = Post.objects.order_by('-id')

        #logger = logging.getLogger('test')
        #logger.error("thisis timerid", team.id)


        return post_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        #post_fixed = Post.objects.filter(isTeams=Post.isTeams).order_by('-registered_date')
        page_numbers_range = 5
        max_index =len(paginator.page_range)
        team = Post.objects.get(pk=self.kwargs["pk"])

        post_fixed = Post.objects.filter(isTeams = team.id)
        context['post_fixed'] = post_fixed
        #teamid = Post.objects.get(pk=team.id)
        #print("PRINT",context_object_name)
        #post_team = Post.objects.get(isTeams = )

        page = self.request.GET.get('page')
        current_page = int(page) if page else 1

        start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
        end_index = start_index + page_numbers_range
        if end_index >= max_index:
            end_index = max_index

        page_range = paginator.page_range[start_index:end_index]
        context['page_range'] = page_range

        return context
def post_detail_view(request, pk):
    user =request.user
    if not user.is_authenticated:
        post_auth = False
        return redirect('/accounts/login')

    """try:
               ismember = Team.objects.get(team_id=pk)
               print(ismember.members.all())

           except ismember.DoesNotExist:
               return HttpResponse(
                       '<script>alert("팀원이 아닙니다.")</script>''<script>location.href="/teams/team_list"</script>')"""
    if user.is_authenticated:
        post = get_object_or_404(Post, pk=pk)
        print("thisis post:",post)

        if request.user == post.writer:
            post_auth = True
        else:
            post_auth = False

        context = {
            'post': post,
            'post_auth': post_auth,
        }
    return render(request, 'shares/post_detail1.html', context)
def post_write_view(request):
    user =request.user
    print("1")
    if not user.is_authenticated:
        post_auth = False
        print("2")
        return redirect('/accounts/login')

    if request.method =="POST":
        form = PostWriteForm(request.POST)
        user_id = User.objects.get(username =user.username)
        print("3")
       # if form.is_valid():
        post = form.save(commit = False)
        print("포스트 입니다",post.article)
        post.writer = user_id


        if request.FILES:
            if 'upload_files' in request.FILES.keys():
                post.filename = request.FILES['upload_files'].name
        post.save(post)

        return redirect('shares:post_list')
    else:
        print("여긴왔다")
        form = PostWriteForm()
    return render(request, "shares/post_write_renew.html", {'form': form})


def post_edit_view(request, pk):
    post = Post.objects.get(id=pk)

    if request.method == "POST":
        #로그인
            form = PostWriteForm(request.POST, instance=post)
            if form.is_valid():
                post = form.save(commit=False)
                post.save()
                messages.success(request, "수정되었습니다.")
                return redirect('/shares/' + str(pk))
    else:
        post = Post.objects.get(id=pk)
        if post.writer == request.user or request.user.level == '0':
            form = PostWriteForm(instance=post)
            context = {
                'form': form,
                'edit': '수정하기',
            }
            return render(request, "shares/post_write_renew.html", context)
        else:
            messages.error(request, "본인 게시글이 아닙니다.")
            return redirect('/shares/' + str(pk))

def post_delete_view(request, pk):
    post = Post.objects.get(id=pk)
    if post.writer == request.user or request.user.level == '0':
        post.delete()
        messages.success(request, "삭제되었습니다.")
        return redirect('/shares/')
    else:
        messages.error(request, "본인 게시글이 아닙니다.")
        return redirect('/shares/' + str(pk))


def post_download_view(request, pk):
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return HttpResponse('<script>alert("File Does not exist.")</script>''<script>location.href="/shares/post_list"</script>')
    #post = get_object_or_404(Post, pk = pk)
    url = post.upload_files.url[1:]
    file_url= urllib.parse.unquote(url)
    print(file_url)
    if os.path.exists(file_url):
        with open(file_url,'rb')as fh:
            quote_file_url = urllib.parse.quote(post.filename.encode('utf-8'))
            response = HttpResponse(fh.read(), content_type=mimetypes.guess_type(file_url)[0])
            response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'%s' % quote_file_url
            return response
        raise Http404
