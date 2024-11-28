from .serializer import AnimeSerializer, GenreSerializer, UserSerializer, User_AnimeSerializer, Anime_GenreSerializer
from .utils import get_user_info, generate_code_challenge, get_data_from_mal_api, check_and_add_anime, get_user_list
from .models import Anime, Genre, User, User_Anime, Anime_Genre
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from rest_framework import viewsets
from django.conf import settings
from datetime import datetime
import pandas as pd
import urllib.parse
import requests
import json
import os
# Create your views here.

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

        user, created = User.objects.get_or_create(
            id=user_info['id'],
            defaults={
                'name': user_info['name'],
                'gender': user_info['gender'],
                'joined_at': joined_at,
                'picture': user_info['picture'],
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token']
            }    
        )

        if not created:
            user.name = user_info['name']
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
    
# tela inicial
@login_required
def me(request):
    user = request.user
    user_info = get_user_info(user)
    return render(request, 'me.html', {'user_info': user_info})

def atualizar_dados(request, username):
    print('Atualizando dados...', username)
    print('='*100)
    try:
        user = User.objects.get(name=username)
        user_info = get_user_info(user)
        user_anime_list_url = f'https://api.myanimelist.net/v2/users/{username}/animelist'
        user_list_json = []
        while user_anime_list_url:
            user_list, user_anime_list_url = get_data_from_mal_api(user_anime_list_url)
            for animes in user_list['data']:
                anime = animes
                anime_id = int(anime['node']['id'])
                check_and_add_anime(anime_id, user_info, anime['list_status'])
            user_list_json += user_list['data']
        user_list_json = json.dumps(user_list['data'])
        print('Atualização concluida com sucesso!')
        return JsonResponse(user_list_json, safe=False)
    except Exception as e:
        print(e)
        return JsonResponse({'error': 'Usuario nao encontrado na base de dados'}, status=400)
    
def get_data_from_username(request, username): 
    try:
        user_list = get_user_list(username)
        return JsonResponse(user_list, safe=False)

    except Exception as e:
        print('error', e)
        return JsonResponse({'error': 'Usuario nao encontrado na base de dados'}, status=400)

def get_difference(request):
    user = request.user
    user_info = get_user_info(user)
    user_list = get_user_list(user_info['name'])
    df = pd.DataFrame(user_list)

    caminho_csv = os.path.join(settings.BASE_DIR, 'mal_api', 'dados', 'animes_frate.csv')
    df_export = pd.read_csv(caminho_csv, delimiter=';')

    diff_df = df_export.merge(df, on='series_title', how='left', indicator=True) 
    only_in_df1 = diff_df[diff_df['_merge'] == 'left_only']['series_title'] # Exibir os valores que estão apenas em df1 print
    print(only_in_df1.tolist())
