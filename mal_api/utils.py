from .models import Anime, User_Anime, User, Anime_Genre, Genre
from datetime import datetime
import requests
import secrets
def get_user_info(user):
    return {
        'id': user.id,
        'name': user.name,
        'gender': user.gender,
        'joined_at': user.joined_at,
        'picture': user.picture,
        'access_token': user.access_token,
        'refresh_token': user.refresh_token
    }

def generate_code_challenge():
    code_challenge = secrets.token_urlsafe(64)
    return code_challenge 

def get_data_from_mal_api(request, username, animelist, user_info):
    user_token = User.objects.get(name='MFrate')
    user_token_info = get_user_info(user_token)
    user_anime_list_url = f'https://api.myanimelist.net/v2/users/{username}/{animelist}'
    headers = {'Authorization': 'Bearer ' + user_token_info['access_token']}
    params = {'fields': 'list_status', 'nsfw': 'True'}
    user_list = {'data': []}
    count = 0
    while user_anime_list_url:
        count += 1
        user_list_response = requests.get(user_anime_list_url, headers=headers, params=params)
        if user_list_response.status_code != 200:
            return user_list_response
        user_list_data = user_list_response.json()
        user_list['data'] += user_list_data['data']
        user_anime_list_url = user_list_data['paging'].get('next')
    return user_list

def get_anime_data_from_mal(mal_id, user_info):
    user_token = User.objects.get(name='MFrate')
    user_token_info = get_user_info(user_token)
    url = f'https://api.myanimelist.net/v2/anime/{mal_id}'
    headers = {'Authorization': 'Bearer ' + user_token_info['access_token']}
    params = {
        'fields': 'id,title,main_picture,mean,media_type,status,genres,my_list_status,num_episodes,source,average_episode_duration,studios,statistics'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return response

def check_and_add_anime(Anime_id, user_info, anime_from_list):
    try:
        anime = Anime.objects.get(id=Anime_id)
        try:
            user_anime = User_Anime.objects.get(user_id=User.objects.get(id=user_info['id']), anime_id=anime)
            #verificar se está atualizado
            verify_user_anime(user_anime, anime_from_list)
            try:
                anime_genres = Anime_Genre.objects.filter(anime=anime)
                return anime

            except Anime_Genre.DoesNotExist:
                anime_data = get_anime_data_from_mal(Anime_id, user_info)
                try:
                    anime_genres = anime_data['genres']
                    for genre in anime_genres:
                        genre_obj, created = Genre.objects.get_or_create(id=genre['id'])
                        Anime_Genre.objects.create(anime=anime, genre=genre_obj)
                except KeyError:
                    pass

        except User_Anime.DoesNotExist:
            add_User_Anime(anime, user_info, anime_from_list)
        return anime
    
    except Anime.DoesNotExist:
        anime, anime_data = add_Anime(Anime_id, user_info)
        add_User_Anime(anime, user_info, anime_from_list)
        try:
            anime_genres = anime_data['genres']
            for genre in anime_genres:
                genre_obj, created = Genre.objects.get_or_create(id=genre['id'], name=genre['name'])
                Anime_Genre.objects.create(anime=anime, genre=genre_obj)
        except KeyError:
            pass
        return anime
   
def add_Anime(Anime_id, user_info):
    anime_data = get_anime_data_from_mal(Anime_id, user_info)
    if anime_data:
        if '"' in anime_data['title']:
            anime_data['title'] = anime_data['title'].replace('"', '')
        anime = Anime.objects.create(
            id=anime_data['id'],
            title=anime_data['title'],
            mean=anime_data.get('mean', None),
            media_type = anime_data['media_type'],
            num_episodes = anime_data['num_episodes'],
            average_episode_duration = anime_data['average_episode_duration'],
            studio = anime_data['studios'][0]['name'] if anime_data['studios'] else None,
            source = anime_data['source']
        )
        print(f"Anime {anime_data['title']} adicionado com sucesso.")
        return anime, anime_data
    else:
        print('Erro ao obter dados do anime na API do MAL.')
        return None

def add_User_Anime(anime, user_info, anime_from_list):
    if 'start_date' in anime_from_list.keys():
        try:
            start_date = datetime.strptime(anime_from_list['start_date'], '%Y-%m-%d').date() if anime_from_list['status'] != 'plan_to_watch' else None
        except:
            start_date = None
    else:
        start_date = None
    if 'finish_date' in anime_from_list.keys():
        try:
            finish_date = datetime.strptime(anime_from_list['finish_date'], '%Y-%m-%d').date() if anime_from_list['status'] == 'completed' else None
        except:
            finish_date = None
    else:
        finish_date = None
    user_anime = User_Anime.objects.create(
        user_id= User.objects.get(id=user_info['id']),
        anime_id=anime,
        status = anime_from_list['status'],
        score = anime_from_list['score'],
        num_episodes_watched = anime_from_list['num_episodes_watched'],
        start_date = start_date,
        finish_date = finish_date  
    )
    print(f"Anime {anime.title} adicionado à lista do usuário {user_info['name']}.")

def verify_user_anime(user_anime, anime_from_list):
    attributes = ['status', 'score', 'num_episodes_watched', 'start_date', 'finish_date']
    update = any(
        getattr(user_anime, attr) != anime_from_list.get(attr)
        for attr in attributes
        if anime_from_list.get(attr) is not None)
    if update:  
        for attr in attributes:
            if anime_from_list.get(attr)is not None:
                setattr(user_anime, attr, anime_from_list[attr])
        user_anime.save()
    

def get_user_list(username):
    #pegar os dados do user_anime e os titulos do anime
    user = User.objects.get(name=username)
    user_info = get_user_info(user)
    user_list = []
    user_anime_list = User_Anime.objects.filter(user_id=user_info['id'])
    for user_anime in user_anime_list:
        anime = Anime.objects.get(id=user_anime.anime_id.id)
        anime_genre_list = Anime_Genre.objects.filter(anime=anime)
        user_list.append({
            'series_title': anime.title,
            'my_status': user_anime.status,
            'my_score': user_anime.score,
            'num_episodes_watched': user_anime.num_episodes_watched,
            'my_start_date': user_anime.start_date,
            'my_finish_date': user_anime.finish_date,
            'series_episodes': anime.num_episodes,
            'series_type': anime.media_type,
            'series_mean': anime.mean,
            'series_source': anime.source,
            'series_studio': anime.studio,
            'average_episode_duration': anime.average_episode_duration,
            'genres': [genre.genre.name for genre in anime_genre_list]

        })
    return user_list