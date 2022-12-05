from django.shortcuts import render
from django.views.generic import ListView
from .models import Post
from django.shortcuts import render,redirect,get_object_or_404
from .forms import PostWriteForm
from accounts.models import User
from django.contrib import messages

#로그인 확인 임포트
#404 임포트
class PostListView(ListView):
    model = Post
    paginate_by = 10
    template_name = 'shares/post_list.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        post_list = Post.objects.order_by('-id')
        return post_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        page_numbers_range = 5
        max_index = len(paginator.page_range)
        post_fixed = Post.objects.filter(top_fixed=True).order_by('-registered_date')
        context['post_fixed'] = post_fixed

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
def post_write_view(request):
    user =request.user

    if not user.is_authenticated:
        post_auth = False
        return redirect('/accounts/login')

    if request.method =="POST":
        form = PostWriteForm(request.POST)
        user_id = User.objects.get(username =user.username)

       # if form.is_valid():
        post = form.save(commit = False)
        print("포스트 입니다",post.article)
        post.writer = user_id

        post.save(post.article)
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
