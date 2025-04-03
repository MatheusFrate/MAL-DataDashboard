from .views import myanimelist_login, my_animelist_callback, me, atualizar_dados, get_data_from_username, get_anime_data
from rest_framework.routers import DefaultRouter
from django.urls import path, include


urlpatterns = [
    #padrão sistema
    path('redirect/', my_animelist_callback, name='redirect'),
    path('login/', myanimelist_login, name='login'),

    #endpoints acessáveis
    path('me/', me, name='me'),
    path('get_data/<str:username>/', get_data_from_username, name='get_data_from_username'),
    path('atualizar_dados/<str:username>/', atualizar_dados, name='atualizar_dados'),
    path('get_anime_data/', get_anime_data, name='get_anime_data'),

]