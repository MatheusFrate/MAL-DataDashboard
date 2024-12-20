# Generated by Django 5.1.3 on 2024-12-01 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mal_api', '0010_rename_num_watched_episodes_user_anime_num_episodes_watched'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnimeList',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('series_title', models.CharField(max_length=255)),
                ('my_status', models.CharField(max_length=255)),
                ('my_score', models.IntegerField()),
                ('num_episodes_watched', models.IntegerField()),
                ('my_start_date', models.DateField(blank=True, null=True)),
                ('my_finish_date', models.DateField(blank=True, null=True)),
                ('series_episodes', models.IntegerField()),
                ('series_type', models.CharField(max_length=255)),
                ('series_mean', models.FloatField()),
                ('series_source', models.CharField(max_length=255)),
                ('series_studio', models.CharField(max_length=255)),
                ('average_episode_duration', models.IntegerField()),
                ('genres', models.CharField(max_length=500)),
                ('user_id', models.IntegerField()),
            ],
            options={
                'db_table': 'anime_list',
                'managed': False,
            },
        ),
    ]
