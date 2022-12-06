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
        team = Team.objects.get(pk=self.kwargs["pk"])
    
        post_list = Post.objects.filter(isTeams=team.id)

        
        return post_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        page_numbers_range = 5
        max_index =len(paginator.page_range)
        team = Team.objects.get(pk=self.kwargs["pk"])

        context['team_id'] = team.id

        print("THIS IS CONTEXT TEAMID ",context)
        #post_fixed = Post.objects.filter(isTeams = team.id)
        #context['post_fixed'] = post_fixed
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

    postid =Post.objects.filter(id=pk)
    print(postid)
    if not user.is_authenticated:
        post_auth = False
        return redirect('/accounts/login')


    if user.is_authenticated:
        post = get_object_or_404(Post, pk=pk)


        if request.user == post.writer:
            post_auth = True
        else:
            post_auth = False

        context = {
            'post': post,
            'post_auth': post_auth,
        }
    return render(request, 'shares/post_detail1.html', context)

def post_write_view(request,pk):
    user = request.user
    team_number = pk
    print("Thsis request method", request.method)
    if not user.is_authenticated:
        post_auth = False
        print("2")
        return redirect('/accounts/login')

    if request.method =="POST":
        form = PostWriteForm(request.POST,request.FILES)
        user_id = User.objects.get(username =user.username)
        #print("form .isteam", form.isTeams)
        #print("team_number", team_number)
        #form.isTeams = team_number

        if form.is_valid():

            post=form.save(commit=False)
            messages.success(request, '성공적으로 등록되었습니다.')
            print("포스트 내용 입니다",post.article)
            print("포스트 제목 입니다", post.title)

            post.writer = user_id
            post.isTeams_id = team_number
        #post.isTeams
            if request.FILES:
                if 'upload_files' in request.FILES.keys():
                    post.filename = request.FILES['upload_files'].name
            post.save()
            return redirect('shares:post_list', pk)

    else:
        print( "team_number:", team_number )
        form = PostWriteForm()


    return render(request, "shares/post_write_renew.html", {'form': form, 'pk':pk})


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
    teamno=post.isTeams_id
    if post.writer == request.user or request.user.level == '0':
        post.delete()
        messages.success(request, "삭제되었습니다.")
        return redirect(f'/shares/{teamno}/')
    else:
        messages.error(request, "본인 게시글이 아닙니다.")
        return redirect(f'/shares/{teamno}' )


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
