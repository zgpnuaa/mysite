from django import template
from django.utils.safestring import mark_safe
import markdown
import time
import datetime
import pytz


register = template.Library()

from article.models import ArticlePost, CommentMulti
from django.db.models import Count


@register.simple_tag
def total_articles():
    return ArticlePost.objects.count()


@register.simple_tag
def author_total_articles(user):
    return user.article.count()


@register.inclusion_tag('article/list/latest_articles.html')
def latest_articles(n=5):
    latest_articles = ArticlePost.objects.order_by("-created")[:n]
    return {"latest_articles": latest_articles}


@register.simple_tag
def most_commented_articles(n=5):
    return ArticlePost.objects.annotate(total_comments=Count('comments')).order_by("-total_comments")[:n]


@register.filter(name='markdown')
def markdown_filter(text):
    return mark_safe(markdown.markdown(text))


@register.simple_tag
def dict_template(h, key):
    if key in h:
        return h[key]
    else:
        return None


TEMP0 = """<div id="%s"  style='margin-left:%spx;margin-top:20px;'><div ><span><img src='%s' class="img-rounded" width='30px'><span style='font-family:SimHei:' class='nickname'>&nbsp;%s</span> <span class="text-muted">说&nbsp;:</span></div><div id="comments_%s" class='comments_content' style="margin-left:50px;margin-top:10px;margin-bottom:10px;font-family:SimHei:"><textarea style="display:none;">%s</textarea></div><div class='children-content text-muted' style="margin-top=30px;"><span>%s</span></span><a style="margin-left:28px;" onclick="like_comment(%s,'like')" href="#"><i class="fas fa-thumbs-up text-muted"> %s</i></a><a style="margin-left:28px;" class="reply" href="javascript:void(0);"><i class="far fa-comment-dots text-muted"></i></a></div><hr>"""


TEMP1 = """<div id="%s"  style='margin-left:%spx;margin-top:20px;'><div ><span><img src='%s' class="img-rounded" width='30px' ><span style='font-family:SimHei:' class='nickname'>&nbsp;%s</span> <span class="text-muted">回复 </span><img src='%s' class="img-rounded" width='30px'><span style='font-family:SimHei:'>&nbsp;%s&nbsp;<span class="text-muted">:</span></span> </div><div id="comments_%s" class='comments_content' style="margin-left:50px;margin-top:10px;margin-bottom:10px;font-family:SimHei;"><textarea style="display:none;">%s</textarea></div><div class='children-content text-muted' style="margin-top=30px;"> <span>%s</span></span><a style="margin-left:28px;" onclick="like_comment(%s,'like')" href="#"><i class="fas fa-thumbs-up text-muted"> %s</i></a><a style="margin-left:28px;" class="reply" href="javascript:void(0);"><i class="far fa-comment-dots text-muted"></i></a></div><hr>"""


def timeago(datetimestamp):
    # dateTimeStamp是一个时间毫秒，注意时间戳是秒的形式，在这个毫秒的基础上除以1000，就是十位数的时间戳。13位数的都是时间毫秒。
    # 把分，时，天，周，半个月，一个月用毫秒表示
    minute = 1000 * 60
    hour = minute * 60
    day = hour * 24
    week = day * 7
    month = day * 30
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.datetime.now()
    now_stamp = int(time.mktime(now.timetuple()))*1000
    # 时间差,东八区和UTC时区相差8小时
    diffvalue = now_stamp - (datetimestamp + 8*60*60*1000)

    if diffvalue < 0:
        return
    # 计算时间差的分，时，天，周，月
    minc = diffvalue/minute
    hourc = diffvalue/hour
    dayc = diffvalue/day
    weekc = diffvalue/week
    monthc = diffvalue/month

    if monthc >= 1 and monthc <= 3:
        result = " " + str(round(monthc)) + "月前"
    elif weekc >= 1 and weekc <= 3:
        result = " " + str(round(weekc)) + "周前"
    elif dayc >= 1 and dayc <= 6:
        result = " " + str(round(dayc)) + "天前"
    elif hourc >= 1 and hourc <= 23:
        result = " " + str(round(hourc)) + "小时前"
    elif minc >= 1 and minc <= 59:
        result = " " + str(round(minc)) + "分钟前"
    elif diffvalue >= 0 and diffvalue <= minute:
        result = "刚刚"
    else:
        result = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    return result



def generate_comment_html(sub_comment_dic, margin_left_val, i):
    html = '<div class="comment">'
    for k, v_dic in sub_comment_dic.items():

        if i == 0:
            html += TEMP1 % (k[0], margin_left_val, k[1][0], k[1][1], k[1][2], k[1][3], k[0],  k[1][4], timeago(k[1][5]), k[0], k[1][6])
        else:
            html += TEMP1 % (k[0], 0, k[1][0], k[1][1], k[1][2], k[1][3], k[0], k[1][4], timeago(k[1][5]), k[0], k[1][6])
        i += 1
        if v_dic:
            html += generate_comment_html(v_dic, margin_left_val, i)
        html += "</div>"
    html += "</div>"
    return html


@register.simple_tag
def tree(comment_dic):

    html = '<div class="comment">'
    for k, v in comment_dic.items():
        if k[2] == "None":
            html += TEMP0 % (k[0], 0, k[1][0], k[1][1], k[0], k[1][4], timeago(k[1][5]), k[0], k[1][6])
        else:
            html += TEMP1 % (k[0], 0, k[1][0], k[1][1], k[1][2], k[1][3], k[0], k[1][4], timeago(k[1][5]), k[0], k[1][6])
        i = 0
        html += generate_comment_html(v, 60, i)
        html += "</div>"
    html += "</div>"

    return mark_safe(html)

