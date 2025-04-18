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

def get_data_from_mal_api(user_anime_list_url):
    user_token = User.objects.get(name='mfrate')
    user_token_info = get_user_info(user_token)
    headers = {'Authorization': 'Bearer ' + user_token_info['access_token']}
    params = {'fields': 'list_status', 'nsfw': 'True'}
    user_list_response = requests.get(user_anime_list_url, headers=headers, params=params)
    if user_list_response.status_code != 200:
        return user_list_response
    user_list_data = user_list_response.json()
    user_anime_list_url = user_list_data['paging'].get('next')
    return user_list_data, user_anime_list_url

def get_anime_data_from_mal(mal_id):
    user_token = User.objects.get(name='mfrate')
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
    except Anime.DoesNotExist:
        anime, anime_data = add_Anime(Anime_id)
        add_User_Anime(anime, user_info, anime_from_list)
        try:
            anime_genres = anime_data['genres']
            for genre in anime_genres:
                genre_obj, created = Genre.objects.get_or_create(id=genre['id'], name=genre['name'])
                Anime_Genre.objects.create(anime=anime, genre=genre_obj)
        except KeyError:
            pass
        return anime

    try:
        user_anime = User_Anime.objects.get(user_id=user_info['id'], anime_id=anime)
        verify_user_anime(user_anime, anime_from_list)
    except User_Anime.DoesNotExist:
        add_User_Anime(anime, user_info, anime_from_list)

    try:
        anime_genres = Anime_Genre.objects.filter(anime=anime)
        return anime
    except Anime_Genre.DoesNotExist:
        anime_data = get_anime_data_from_mal(Anime_id)
        try:
            anime_genres = anime_data['genres']
            for genre in anime_genres:
                genre_obj, created = Genre.objects.get_or_create(id=genre['id'])
                Anime_Genre.objects.create(anime=anime, genre=genre_obj)
        except KeyError:
            pass
   
def add_Anime(Anime_id):
    anime_data = get_anime_data_from_mal(Anime_id)
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
            source = anime_data['source'] if 'source' in anime_data else None
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
    User_Anime.objects.create(
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
                if attr == 'start_date' or attr == 'finish_date':
                    try:
                        date = datetime.strptime(anime_from_list[attr], '%Y-%m-%d').date()
                        setattr(user_anime, attr, date)
                    except:
                        setattr(user_anime, attr, None)
                else:
                     setattr(user_anime, attr, anime_from_list.get(attr))
        user_anime.save()
    