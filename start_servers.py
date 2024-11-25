import subprocess
import os

def start_django():
    subprocess.Popen(['../.venv/Scripts/python', 'manage.py', 'runserver'])

def start_streamlit():
    os.chdir('./mal_api')  # Altere para o diretório do seu aplicativo Django
    subprocess.Popen(['streamlit', 'run', 'dash_app.py'])

if __name__ == '__main__':
    start_django()
    start_streamlit()
