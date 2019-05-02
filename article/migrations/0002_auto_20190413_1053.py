# Generated by Django 2.1.7 on 2019-04-13 02:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('article', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commentmulti',
            name='Pid',
        ),
        migrations.RemoveField(
            model_name='commentmulti',
            name='article',
        ),
        migrations.RemoveField(
            model_name='commentmulti',
            name='content',
        ),
        migrations.RemoveField(
            model_name='commentmulti',
            name='ctime',
        ),
        migrations.RemoveField(
            model_name='commentmulti',
            name='like',
        ),
        migrations.RemoveField(
            model_name='commentmulti',
            name='user',
        ),
        migrations.AddField(
            model_name='commentmulti',
            name='comment_article',
            field=models.ForeignKey(null='true', on_delete=django.db.models.deletion.CASCADE, related_name='comment_article', to='article.ArticlePost'),
            preserve_default='true',
        ),
        migrations.AddField(
            model_name='commentmulti',
            name='comment_content',
            field=models.TextField(null='true'),
            preserve_default='true',
        ),
        migrations.AddField(
            model_name='commentmulti',
            name='comment_like',
            field=models.ManyToManyField(blank=True, related_name='comment_like', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='commentmulti',
            name='comment_parent_id',
            field=models.CharField(max_length=300, null='true'),
            preserve_default='true',
        ),
        migrations.AddField(
            model_name='commentmulti',
            name='comment_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='commentmulti',
            name='comment_user',
            field=models.ForeignKey(null='true', on_delete=django.db.models.deletion.CASCADE, related_name='comment_user', to=settings.AUTH_USER_MODEL),
            preserve_default='true',
        ),
    ]
