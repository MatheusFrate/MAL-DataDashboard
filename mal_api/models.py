from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .choices import STATUS_CHOICHES
def validate_score(value):
    if value < 0 or value > 10:
        raise ValidationError(
            _('%(value)s is not an integer between 0 and 10'),
            params={'value': value},
        )

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, name, gender, joined_at, picture, password=None):
        if not name:
            raise ValueError("Users must have a name")
        user = self.model(
            name=name,
            gender=gender,
            joined_at=joined_at,
            picture=picture
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, name, gender, joined_at, picture, password=None):
        user = self.create_user(
            name=name,
            gender=gender,
            joined_at=joined_at,
            picture=picture,
            password=password
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    gender = models.CharField(max_length=10)
    joined_at = models.DateField()
    picture = models.CharField(max_length=100)
    access_token = models.CharField(max_length=100, blank=True, null=True)
    refresh_token = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, default='default_password')
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'name'

    def __str__(self):
        return self.name
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        return self.is_superuser


class Anime(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    mean = models.FloatField(null=True, blank=True)
    media_type = models.CharField(max_length=20)
    num_episodes = models.IntegerField()
    average_episode_duration = models.FloatField()
    studio = models.CharField(max_length=100, null=True, blank=True)
    source = models.CharField(max_length=100)

    def __str__(self):
        return self.title
    
class Genre(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    

class User_Anime(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    anime_id = models.ForeignKey(Anime, on_delete=models.CASCADE)
    score = models.FloatField(validators=[validate_score], null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICHES)

    num_episodes_watched = models.IntegerField(null=True)
    start_date = models.DateField(null=True, blank=True)
    finish_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user_id.name + ' ' + self.anime_id.title
    
class Anime_Genre(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.anime.title} - {self.genre.name}'
    

class AnimeList(models.Model):
    id = models.AutoField(primary_key=True)
    series_title = models.CharField(max_length=255)
    my_status = models.CharField(max_length=255)
    my_score = models.IntegerField()
    num_episodes_watched = models.IntegerField()
    my_start_date = models.DateField(null=True, blank=True)
    my_finish_date = models.DateField(null=True, blank=True)
    series_episodes = models.IntegerField()
    series_type = models.CharField(max_length=255)
    series_mean = models.FloatField()
    series_source = models.CharField(max_length=255)
    series_studio = models.CharField(max_length=255)
    average_episode_duration = models.IntegerField()
    genres = models.CharField(max_length=500)
    user_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'anime_list'