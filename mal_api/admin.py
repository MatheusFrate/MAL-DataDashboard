from django.contrib import admin
from .models import User, Anime, User_Anime, Genre, Anime_Genre
# Register your models here.
admin.site.register(User)
admin.site.register(Anime)
admin.site.register(User_Anime)
admin.site.register(Genre)
admin.site.register(Anime_Genre)