from .serializer import AnimeSerializer, GenreSerializer, UserSerializer, User_AnimeSerializer, Anime_GenreSerializer
from .utils import get_user_info, generate_code_challenge, get_data_from_mal_api, check_and_add_anime, get_anime_data_from_mal
from .models import Anime, Genre, User, User_Anime, Anime_Genre, AnimeList
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import render, redirect
from django.contrib.auth import login
from rest_framework import viewsets
from django.db import transaction
from datetime import datetime
import urllib.parse
import requests
import os

class AnimeViewSet(viewsets.ModelViewSet):
    queryset = Anime.objects.all()
    serializer_class = AnimeSerializer

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class User_AnimeViewSet(viewsets.ModelViewSet):
    queryset = User_Anime.objects.all()
    serializer_class = User_AnimeSerializer

class Anime_GenreViewSet(viewsets.ModelViewSet):
    queryset = Anime_Genre.objects.all()
    serializer_class = Anime_GenreSerializer



# Função para realizar o login
def myanimelist_login(request):
  
    code_challenge = generate_code_challenge()
    code_challenge_method = 'plain'
    request.session['code_verifier'] = code_challenge
    params = {
        'response_type': 'code',
        'client_id': os.getenv('CLIENT_ID'),
        'redirect_uri': os.getenv('REDIRECT_URI'),
        'code_challenge': code_challenge,
        'code_challenge_method': code_challenge_method
    }

    url = 'https://myanimelist.net/v1/oauth2/authorize?' + urllib.parse.urlencode(params)
    return redirect(url)

# Função de callback do login
def my_animelist_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')

    if code:
        token_url = os.getenv('TOKEN_URL')
        data = {
            'client_id': os.getenv('CLIENT_ID'),
            'client_secret': os.getenv('CLIENT_SECRET'),
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': os.getenv('REDIRECT_URI'),
            'code_verifier': request.session['code_verifier']
        }
        response = requests.post(token_url, data=data)
        tokens = response.json()

        if tokens.get('error'):
            return HttpResponse('Erro ao realizar login')
        
        user_info_url = 'https://api.myanimelist.net/v2/users/@me'
        headers = {'Authorization': 'Bearer ' + tokens['access_token']}
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()

        joined_at_str = user_info['joined_at']
        joined_at = datetime.strptime(joined_at_str, '%Y-%m-%dT%H:%M:%S%z').date() if joined_at_str else None
        name = str(user_info['name']).lower()
        user, created = User.objects.get_or_create(
            id=user_info['id'],
            defaults={
                'name': name,
                'gender': user_info['gender'],
                'joined_at': joined_at,
                'picture': user_info['picture'],
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token']
            }    
        )

        if not created:
            user.name = name
            user.gender = user_info['gender']
            user.joined_at = joined_at
            user.picture = user_info['picture']
            user.access_token = tokens['access_token']
            user.refresh_token = tokens['refresh_token']
            user.save()

        login(request, user)
        

        return redirect('me')
    else:
        return HttpResponse('Erro ao realizar login')
    
# tela que mostra dados do usuario logado
@login_required
def me(request):
    user = request.user
    user_info = get_user_info(user)
    return render(request, 'me.html', {'user_info': user_info})

#Atualiza os dados da base de dados, recebendo da API do MyAnimeList
@swagger_auto_schema(
    method='get',
    operation_description="Atualiza os dados de um usuário.",
    responses={200: 'Dados atualizados com sucesso.', 400: 'Erro na atualização.'},
)
@api_view(['GET'])
def atualizar_dados(request, username):
    print('Atualizando dados...', username)
    print('='*100)
    try:
        username = username.lower()
    except Exception as e:
        print(e)
        return JsonResponse({'error': 'digite o nome do usuario'})
    try:
        user = User.objects.get(name=username)
        user_info = get_user_info(user)
        user_anime_list_url = f'https://api.myanimelist.net/v2/users/{username}/animelist'
        while user_anime_list_url:
            user_list, user_anime_list_url = get_data_from_mal_api(user_anime_list_url) 
            
            with transaction.atomic():
                for anime in user_list['data']:
                    anime_id = int(anime['node']['id'])
                    check_and_add_anime(anime_id, user_info, anime['list_status'])
        print('Atualização concluida com sucesso!')
        return JsonResponse({'message': 'Atualização concluída com sucesso!'}, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({'error': 'Usuario nao encontrado na base de dados'}, status=400)

#retorna os dados do usuário apartir de uma view 
@swagger_auto_schema(
    method='get',
    operation_description="Busca os dados do usuário.",
    responses={200: 'Dados buscados com sucesso.', 400: 'Erro na busca.'},
    security=[]
) 
@api_view(['GET'])
def get_data_from_username(request, username): 
    try:
        username = username.lower()
    except Exception as e:
        print(e)
        return JsonResponse({'error': 'digite o nome do usuario'})
    try:
        user = User.objects.get(name=username)
        user_list = AnimeList.objects.filter(user_id = user.id)
        data = list(user_list.values(
            'series_title', 'my_status', 'my_score', 'num_episodes_watched', 'my_start_date', 'my_finish_date', 'series_episodes', 'series_type', 'series_mean', 'series_source', 'series_studio', 'average_episode_duration', 'genres' 
        ))
        return JsonResponse(data, safe=False)

    except Exception as e:
        print('error', e)
        return JsonResponse({'error': 'Usuario nao encontrado na base de dados'}, status=400)


@swagger_auto_schema(
    method='get',
    operation_description="Busca os dados do anime na API do MAL.",
    responses={200: 'Dados buscados com sucesso.', 400: 'Erro na busca.'},
    security=[]
) 
@api_view(['GET'])
def get_anime_data(request):
    anime_titles = request.query_params.getlist('names', None)
    capas = []
    for i in anime_titles:
        i = i.strip(" '[]\"")
        if i[0] == ' ':
            i = i[1:]
        anime = Anime.objects.filter(title__icontains=i).first()
        data = get_anime_data_from_mal(anime.id)
        capas.append(data['main_picture']['medium'])
    return JsonResponse(capas, safe=False)
