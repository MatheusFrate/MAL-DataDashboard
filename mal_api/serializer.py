from rest_framework import serializers
from .models import Anime, Genre, User, User_Anime, Anime_Genre

class AnimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anime
        fields = '__all__'

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class User_AnimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_Anime
        fields = '__all__'

class Anime_GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anime_Genre
        fields = '__all__'