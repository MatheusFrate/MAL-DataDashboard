from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnimeViewSet, GenreViewSet, UserViewSet, User_AnimeViewSet, Anime_GenreViewSet, myanimelist_login, my_animelist_callback, me, atualizar_dados, get_data_from_username

router = DefaultRouter()
router.register('anime/', AnimeViewSet)
router.register('genre/', GenreViewSet)
router.register('user/', UserViewSet)
router.register('user_anime/', User_AnimeViewSet)
router.register('anime_genre/', Anime_GenreViewSet)

urlpatterns = [
    #padrão sistema
    path('redirect/', my_animelist_callback, name='redirect'),
    path('login/', myanimelist_login, name='login'),
    path('api/', include(router.urls)),

    #endpoints acessáveis
    path('me/', me, name='me'),
    path('get_data/<str:username>/', get_data_from_username, name='get_data_from_username'),
    path('atualizar_dados/<str:username>/', atualizar_dados, name='atualizar_dados'),
]