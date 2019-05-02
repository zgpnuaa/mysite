from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import ArticlePost, CommentMulti
from .forms import CommentForm, CommentMultiForm
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
import redis
from django.conf import settings
from django.db.models import Count
import collections
import json
from account.models import UserInfo
import time
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import Iterable


r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


def article_titles(request, username=None):
    num_views = {}
    if username:
        user = User.objects.get(username=username)
        articles_title = ArticlePost.objects.filter(author=user)
        try:
            userinfo = user.userinfo
        except:
            userinfo = None
    else:
        articles_title = ArticlePost.objects.all()
    all_views = {}
    all_comments = {}
    for article in articles_title:
        comment_list1 = list(CommentMulti.objects.values().filter(comment_article=article))
        all_comments[article] = len(comment_list1)
        if r.get("article:{}:views".format(article.id)):
            total_views = int(r.get("article:{}:views".format(article.id)))
        else:
            total_views = 0
        all_views[article] = total_views
    paginator = Paginator(articles_title, 5)
    page = request.GET.get('page')
    try:
        current_page = paginator.page(page)
        articles = current_page.object_list
    except PageNotAnInteger:
        current_page = paginator.page(1)
        articles = current_page.object_list
    except EmptyPage:
        current_page = paginator.page(paginator.num_pages)
        articles = current_page.object_list
    if username:
        return render(request, "article/list/author_articles.html", {"articles": articles, "page": current_page, "userinfo": userinfo, "user": user, "all_views": all_views, "all_comments": all_comments})
    return render(request, "article/list/article_titles.html", {"articles": articles, "page": current_page, "all_views": all_views, "all_comments": all_comments})


def tree_search(d_dic, comment_obj):
    for k, v_dic in d_dic.items():
        if k[0] == int(comment_obj[2]):
            d_dic[k][comment_obj] = collections.OrderedDict()
            return
        else:
            tree_search(d_dic[k], comment_obj)


comment_list = [
    (1, ('com1', 'com2', 'content', 'c_time', 'like'), None),
    (2, ('com1', 'com2', 'content', 'c_time', 'like'), None),
    (3, ('com1', 'com2', 'content', 'c_time', 'like'), None),
    (9, ('com1', 'com2', 'content', 'c_time', 'like'), 5),
    (4, ('com1', 'com2', 'content', 'c_time', 'like'), 2),
    (5, ('com1', 'com2', 'content', 'c_time', 'like'), 1),
    (6, ('com1', 'com2', 'content', 'c_time', 'like'), 4),
    (7, ('com1', 'com2', 'content', 'c_time', 'like'), 2),
    (8, ('com1', 'com2', 'content', 'c_time', 'like'), 4),
]

# list-> ordereddict
def build_tree(comment_list):
    comment_dic = collections.OrderedDict()

    for comment_obj in comment_list:
        if comment_obj[2] == "None":
            comment_dic[comment_obj] = collections.OrderedDict()
        else:
            tree_search(comment_dic, comment_obj)
    #print(comment_dic)
    return comment_dic

@csrf_exempt
def article_detail(request, id, slug):
    article = get_object_or_404(ArticlePost, id=id, slug=slug)
    total_views = r.incr("article:{}:views".format(article.id))
    r.zincrby('article_ranking',  1, article.id)

    article_ranking = r.zrange('article_ranking', 0, -1, desc=True)[:10]
    article_ranking_ids = [int(id) for id in article_ranking]
    most_viewed = list(ArticlePost.objects.filter(id__in=article_ranking_ids))
    most_viewed.sort(key=lambda x: article_ranking_ids.index(x.id))

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        commentmulti_form = CommentMultiForm()
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.article = article
            new_comment.save()
        if request.is_ajax():
            comment = json.loads(request.POST.get("comment"))
            new_commentmulti = commentmulti_form.save(commit=False)
            new_commentmulti.comment_article = article
            new_commentmulti.comment_parent_id = comment["comment_parent_id"]
            new_commentmulti.comment_content = comment["comment_content"]
            new_commentmulti.comment_user = request.user
            new_commentmulti.save()
        return HttpResponse(json.dumps({"success": "1"}))
    else:
        comment_list1 = list(CommentMulti.objects.values().filter(comment_article=article))
        comment_lst = []
        for comment in comment_list1:
            comment_id = comment['id']
            comment_user = User.objects.get(id=comment['comment_user_id'])
            if comment['comment_parent_id'] == "None":
                parent_comment_user = None
                parent_comment_user_obj = None
            if comment['comment_parent_id'] != "None":
                parent_comment = list(CommentMulti.objects.values().filter(id=comment['comment_parent_id']))
                parent_comment_user = str(User.objects.get(id=parent_comment[0]['comment_user_id']))
                parent_comment_user_obj = User.objects.get(id=parent_comment[0]['comment_user_id'])
            comment_content = comment['comment_content']
            comment_time = int(round(time.mktime(comment['comment_time'].timetuple())*1000))
            comment_obj = CommentMulti.objects.get(id=comment_id)
            # count后记得加括号->count(),不加括号调用方法本身，带括号调用方法的返回值
            comment_like = int(comment_obj.comment_like.count())
            comment_user_info = UserInfo.objects.get(user=comment_user)
            comment_user_photo = comment_user_info.photo
            try:
                parent_comment_user_info = UserInfo.objects.get(user=parent_comment_user_obj)
            except:
                parent_comment_user_info = None
            if parent_comment_user_info:
                if parent_comment_user_info.photo:
                    parent_comment_user_photo = parent_comment_user_info.photo
                else:
                    parent_comment_user_photo = None
            else:
                parent_comment_user_photo = None
            comment_tup = (comment_id, (comment_user_photo, comment_user, parent_comment_user_photo, parent_comment_user, comment_content, comment_time, comment_like), comment['comment_parent_id'])
            comment_lst.append(comment_tup)

        comment_dic = build_tree(comment_lst)
        # 有序字典按父评论发表时间进行倒序排列，即最新发布的评论排在前面
        comment_dic_reverse = collections.OrderedDict(sorted(comment_dic.items(), key=lambda t: t[0][1][5], reverse=True))
        # 评论分页
        num_per = 5
        paginator = Paginator(list(comment_dic_reverse.items()), num_per)
        page = request.GET.get('page')
        try:
            current_page = paginator.page(page)
            comment_dic_reverse_lst = current_page.object_list
            comment_dic_reverse_p = collections.OrderedDict()
            for sub_list in comment_dic_reverse_lst:
                comment_dic_reverse_p[sub_list[0]] = sub_list[1]

        except PageNotAnInteger:
            current_page = paginator.page(1)
            comment_dic_reverse_lst = current_page.object_list
            comment_dic_reverse_p = collections.OrderedDict()
            for sub_list in comment_dic_reverse_lst:
                comment_dic_reverse_p[sub_list[0]] = sub_list[1]
        except EmptyPage:
            current_page = paginator.page(paginator.num_pages)
            comment_dic_reverse_lst = current_page.object_list
            comment_dic_reverse_p = collections.OrderedDict()
            for sub_list in comment_dic_reverse_lst:
                comment_dic_reverse_p[sub_list[0]] = sub_list[1]

        comment_form = CommentForm()

        article_tags_ids = article.article_tag.values_list("id", flat=True)
        similar_articles = ArticlePost.objects.filter(article_tag__in=article_tags_ids).exclude(id=article.id)
        similar_articles = similar_articles.annotate(same_tags=Count("article_tag")).order_by('-same_tags', '-created')[:4]

        return render(request, "article/list/article_detail.html", {"article": article, "total_views": total_views, "most_viewed": most_viewed, "comment_form": comment_form, "similar_articles": similar_articles, "comment_dic": comment_dic_reverse_p, "num_comments": len(comment_lst), "page": current_page})


@login_required(login_url='/account/login/')
@require_POST
@csrf_exempt
def like_article(request):
    article_id = request.POST.get('id')
    action = request.POST.get('action')
    if article_id and action:
        try:
            article = ArticlePost.objects.get(id=article_id)
            if action == "like":
                article.users_like.add(request.user)
                return HttpResponse("1")
            else:
                article.users_like.remove(request.user)
                return HttpResponse("2")
        except:
            return HttpResponse("no")


@login_required(login_url='/account/login/')
@require_POST
@csrf_exempt
def like_comment(request):
    comment_id = request.POST.get('comment_id')
    action = request.POST.get('action')
    if comment_id and action:
        try:
            comment = CommentMulti.objects.get(id=comment_id)
            if action == "like":
                comment.comment_like.add(request.user)
                return HttpResponse("1")
            else:
                comment.users_like.remove(request.user)
                return HttpResponse("2")
        except:
            return HttpResponse("no")
