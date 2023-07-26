from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from .models import Blog, BlogType, ReadNum
from comment.models import Comment
from comment.forms import CommentForm


def get_blog_list_common_data(request, blogs_all_list):
    paginator = Paginator(blogs_all_list, 3)
    page_num = request.GET.get('page', 1)
    page_of_blogs = paginator.get_page(page_num)
    currentr_page_num = page_of_blogs.number
    page_range = list(range(max(currentr_page_num - 2, 1), currentr_page_num)) + \
                 list(range(currentr_page_num, min(currentr_page_num + 2, paginator.num_pages)))
    if page_range[0] - 1 >= 2:
        page_range.insert(0, '...')
    if paginator.num_pages - page_range[-1] >= 2:
        page_range.append('...')
    if page_range[0] != 1:
        page_range.insert(0, 1)
    if page_range[-1]:
        page_range.append(paginator.num_pages)

    context = {}
    context['blogs'] = page_of_blogs.object_list
    context['page_of_blogs'] = page_of_blogs
    context['page_range'] = page_range
    context['blog_types'] = BlogType.objects.annotate(blog_count=Count('blog'))
    context['blog_dates'] = Blog.objects.dates('created_time', 'month', order='DESC') \
        .annotate(blog_count=Count('created_time'))
    return context


def blog_list(request):
    # 获取页码参数
    blogs_all_list = Blog.objects.all()
    context = get_blog_list_common_data(request, blogs_all_list)
    return render(request, 'blog_list.html', context)


def blog_detail(request, blog_pk):
    blog = get_object_or_404(Blog, pk=blog_pk)
    if not request.COOKIES.get('blog_%s_readed' % blog_pk):
        if ReadNum.objects.filter(blog=blog).count():
            # 存在记录
            readnum = ReadNum.objects.get(blog=blog)
        else:
            # 不存在记录
            readnum = ReadNum(blog=blog)
        readnum.read_num += 1
        readnum.save()

    blog_content_type = ContentType.objects.get_for_model(blog)
    comments = Comment.objects.filter(content_type=blog_content_type, object_id=blog_pk, parent=None)

    context = {}
    context['previous_blog'] = Blog.objects.filter(created_time__gt=blog.created_time).last()
    context['next_blog'] = Blog.objects.filter(created_time__lt=blog.created_time).first()
    context['blog'] = blog
    context['comments'] = comments.order_by('-comment_time')
    data={}
    data['content_type'] = blog_content_type.model
    data['object_id'] = blog_pk
    context['comment_form'] = CommentForm(initial={'content_type': blog_content_type.model, 'object_id': blog_pk, 'reply_comment_id': 0})
    response = render(request, 'blog_detail.html', context)
    response.set_cookie('blog_%s_readed' % blog_pk, 'true')
    return response


def blogs_with_type(request, blog_type_pk):
    blog_type = get_object_or_404(BlogType, pk=blog_type_pk)
    blogs_all_list = Blog.objects.filter(blog_type=blog_type)
    context = get_blog_list_common_data(request, blogs_all_list)
    context['blog_type'] = blog_type
    return render(request, 'blogs_with_type.html', context)


def blogs_with_date(request, year, month):
    blogs_all_list = Blog.objects.filter(created_time__year=year, created_time__month=month)
    context = get_blog_list_common_data(request, blogs_all_list)
    context['blogs_with_date'] = '%s年%s月' % (year, month)
    return render(request, 'blogs_with_date.html', context)
