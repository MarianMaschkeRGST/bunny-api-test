from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()

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

    def get_course_progress_for_user(self, user):
        """Calculate how much of the course the current user has completed"""
        videos = self.video_set.all()
        if not videos:
            return 0
            
        total_progress = 0
        for video in videos:
            try:
                progress = video.videoprogress_set.get(user=user)
                total_progress += progress.watch_progress
            except VideoProgress.DoesNotExist:
                continue
        return round(total_progress / videos.count())
    
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

    def get_progress_for_user(self, user):
        """Show video progress for user"""
        try:
            progress = self.videoprogress_set.get(user=user)
            return progress.watch_progress
        except VideoProgress.DoesNotExist:
            return 0

    def __str__(self):
        return self.title
    

class VideoProgress(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='ユーザー',
        on_delete=models.CASCADE,
    )
    video = models.ForeignKey(
        Video,
        verbose_name='動画',
        on_delete=models.CASCADE,
    )
    watch_progress = models.IntegerField(
        verbose_name='進捗',
        default=0,
        validators=[
            MaxValueValidator(100),
            MinValueValidator(0)
        ]
    )
    created_at = models.DateTimeField(
        verbose_name='登録日',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='更新日',
        auto_now=True,
    )

    class Meta:
        verbose_name = '進捗'
        verbose_name_plural = '視聴進捗'
        unique_together = ['user', 'video']

    def __str__(self):
        return f"{self.user.username} - {self.video.title} - {self.watch_progress}%"