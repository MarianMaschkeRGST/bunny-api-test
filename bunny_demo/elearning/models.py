from django.db import models

class Course(models.Model):
    name = models.CharField(
        verbose_name='講座名',
        max_length=256,
    )
    bunny_collection_id = models.CharField(
        verbose_name='bunny collection id',
        max_length=64,
    )
    created_at = models.DateTimeField(
        verbose_name='登録日',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='更新日',
        auto_now=True,
    )

    def __str__(self):
        return self.name
    
class Video(models.Model):

    course = models.ForeignKey(
        Course,
        verbose_name='講座',
        on_delete=models.CASCADE,
    )
    bunny_video_id = models.CharField(
        verbose_name='bunny video id',
        max_length=64,
    )
    title = models.CharField(
        verbose_name='動画タイトル',
        max_length=256,
    )
    duration = models.IntegerField(
        verbose_name='時間（分）',
        default=0
    )
    description = models.TextField(
        verbose_name='備考',
        default='',
        blank=True,
    )
    created_at = models.DateTimeField(
        verbose_name='登録日',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='更新日',
        auto_now=True,
    )

    def __str__(self):
        return self.title