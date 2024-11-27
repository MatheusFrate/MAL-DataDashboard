import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import calendar
import numpy as np


st.set_page_config(layout="wide")
st.title("Dashboard de Séries de Animes")
st.markdown("Este dashboard apresenta uma análise de séries de animes, incluindo notas, status e quantidade de episódios.")
st.markdown("---")

#region sidebar - api
# Carregamento do dataset
def enviar_requisicao(input_text):
    st.markdown( 
        f""" 
            <h1>
                <a href="https://myanimelist.net/profile/{input_text}" target="_blank" style="text-decoration: none; color: inherit;">
                    Perfil: {input_text}
                </a>
            </h1> 
        """, unsafe_allow_html=True )
    response = requests.get(f'http://localhost:8000/api/get_data/{input_text}')
    if response.status_code == 200:
        df = pd.DataFrame(response.json())
        if df.empty:
            st.warning("Nenhum dado encontrado para o perfil informado.")
            st.session_state.clear()
        else:
            st.session_state['df'] = df
    else:
        error_message = response.json()
        st.error(f'Erro ao enviar a requisição. {error_message.get("error", "")}')

def atualizar_dados(input_text_2):
    response = requests.get(f'http://localhost:8000/api/atualizar_dados/{input_text_2}', timeout=300)
    if response.status_code == 200:
        enviar_requisicao(input_text_2)
    else:
        error_message = response.json()
        st.error(f'Erro ao enviar a requisição. {error_message.get("error", "")}')

input_text = st.sidebar.text_input("Digite o perfil a ser analisado:")
if st.sidebar.button('Buscar dados'):
    enviar_requisicao(input_text)

if st.sidebar.button('Atualizar dados'):
    atualizar_dados(input_text)
#endregion

# Verificar se o DataFrame existe no session_state
if 'df' in st.session_state:
    df = st.session_state['df']
    
    # region Filtros
    # Criação de grupos de datas
    df['my_finish_date'] = pd.to_datetime(df['my_finish_date'], errors='coerce')
    df['my_start_date'] = pd.to_datetime(df['my_start_date'], errors='coerce')
    YearMonth = df['my_finish_date'].apply(lambda x: 'Sem data' if pd.isnull(x) else str(x.year) + '-' + str(x.month))
    month_options = YearMonth.unique().tolist()
    month_options = [x if x != 'nan-nan' else 'Sem data' for x in month_options]

    # Criação de grupos de episódios
    bins = [-float('inf'), 1, 2, 7, 14, 27, 53, 101, float('inf')]  # Intervalo para 0, 1, 2-6, 7-13, etc.
    labels = ['0', '1', '2-6', '7-13', '14-26', '27-52', '53-100', '100+']
    df['episode_range'] = pd.cut(df['series_episodes'], bins=bins, labels=labels, right=False)
    range_options = ["Mostrar todos"] + df['episode_range'].unique().tolist()

    # Criação de grupos de status
    status_options = ["Mostrar todos"] + df['my_status'].unique().tolist()

    # Criação de grupos de tipos de séries
    series_type_options = ["Mostrar todos"] + df['series_type'].unique().tolist()

    # Criação de grupos de studios
    studios_options = ["Mostrar todos"] + df['series_studio'].unique().tolist()

    genres_options = df['genres'].explode().unique().tolist()

    month = st.sidebar.selectbox('Selecione o mês', ["Mostrar todos"] + sorted(month_options, reverse=True), key='month')
    range_episodes = st.sidebar.selectbox('Selecione o range de episódios', range_options, key='range_episodes')
    status = st.sidebar.selectbox('Selecione o status', status_options, key='status')
    series_type = st.sidebar.selectbox('Selecione o tipo de série', series_type_options, key='series_type')
    studios = st.sidebar.selectbox('Selecione o studio', studios_options, key='studios')
    genres = st.sidebar.multiselect('Selecione os gêneros', genres_options, key='genres')

    def reset():
        st.session_state.month = "Mostrar todos"
        st.session_state.range_episodes = "Mostrar todos"
        st.session_state.status = "Mostrar todos"
        st.session_state.series_type = "Mostrar todos"
        st.session_state.studios = "Mostrar todos"
        st.session_state.genres = []

    st.sidebar.button('Limpar Filtros', on_click=reset)

    if month == "Mostrar todos":
        df_filtered = df.reset_index(drop=True)
    else:
        df = df.sort_values("my_finish_date", ascending=True)
        df_filtered = df[YearMonth == month].reset_index(drop=True)
    if range_episodes == "Mostrar todos":
        df_filtered = df_filtered.reset_index(drop=True)
    else:
        df_filtered = df_filtered[df_filtered['episode_range'] == range_episodes].reset_index(drop=True)
    if status == "Mostrar todos":
        df_filtered = df_filtered.reset_index(drop=True)
    else:
        df_filtered = df_filtered[df_filtered['my_status'] == status].reset_index(drop=True)
    if series_type == "Mostrar todos":
        df_filtered = df_filtered.reset_index(drop=True)
    else:
        df_filtered = df_filtered[df_filtered['series_type'] == series_type].reset_index(drop=True)
    if studios == "Mostrar todos":
        df_filtered = df_filtered.reset_index(drop=True)
    else:
        df_filtered = df_filtered[df_filtered['series_studio'] == studios].reset_index(drop=True)
    if not genres:
        df_filtered = df_filtered.reset_index(drop=True)
    else:
        df_filtered = df_filtered[df_filtered['genres'].apply(lambda x: any(item in genres for item in x))].reset_index(drop=True)
    
    filtros = [ month if month != "Mostrar todos" else "", range_episodes if range_episodes != "Mostrar todos" else "", status if status != "Mostrar todos" else "", series_type if series_type != "Mostrar todos" else "", studios if studios != "Mostrar todos" else "",", ".join(genres) if genres and "Mostrar todos" not in genres else "" ]
    if any(filtros): 
        filtros_aplicados = f'filtros aplicados: {", ".join([filtro for filtro in filtros if filtro])}' 
        st.subheader(filtros_aplicados) 
    else: 
        st.subheader("Nenhum filtro aplicado.")
    # endregion

    #  region Criação de colunas
    st.header('Dados')
    total_anime, animes_avaliados, nota_media, nota_maxima, nota_minima, nota_mediana = st.columns(6)
    episodios_assistidos, card8 = st.columns(2)
    st.markdown("---")

    st.header('Gráficos')
    graph_serie_episodio_nota,  graph_series_data_conclusao = st.columns(2)
    st.markdown("---")
    graph_series_tipo, graph_nota_tipo  = st.columns(2)
    st.markdown("---")
    graph_series_status, graph_series_genero  = st.columns(2)
    st.markdown("---")
    graph_tempo_nota, card_tempo_gasto_total, graph_serie_nota  = st.columns([3,1,3]) #isso é um ajuste de proporção - o card tem que ser menor
    st.markdown("---")
    graph_heatmap = st.container()
    st.markdown("---")
    graph_timeline = st.container()
    st.markdown("---")
    #endregion

    # region card
    total_series = df_filtered['series_title'].count()
    total_scored_series = df_filtered[df_filtered['my_score'] != 0]['series_title'].count()
    average_score = df_filtered[df_filtered['my_score'] != 0]['my_score'].mean()
    total_anime.metric("Total de animes", total_series)
    animes_avaliados.metric("Animes Avaliadas", total_scored_series)
    nota_media.metric("Nota Média", round(average_score, 2) if not pd.isnull(average_score) else 'Sem dados')
    nota_maxima.metric("Nota Máxima", df_filtered['my_score'].max() if not pd.isnull(average_score) else 'Sem dados')
    nota_minima.metric("Nota Mínima", df_filtered[df_filtered['my_score'] != 0]['my_score'].min() if not pd.isnull(average_score) else 'Sem dados')
    nota_mediana.metric("Nota Mediana", df_filtered['my_score'].median() if not pd.isnull(average_score) else 'Sem dados')
    episodios_assistidos.metric("episódios assistidos", df_filtered['num_episodes_watched'].sum())
    # endregion

    #region gráfico de barras da quantidade de séries por Nota
    df_group_score = df_filtered.groupby('my_score', as_index=False, observed=True)['series_title'].count()
    fig_score = go.Figure()
    fig_score.add_trace(go.Bar(
        x=df_group_score['my_score'],
        y=df_group_score['series_title'],
        name='Quantidade de Séries',
    ))
    fig_score.update_layout(
        title='Quantidade de Séries por Nota',
        xaxis_title='Nota',
        yaxis_title='Quantidade de Séries',
        yaxis=dict(
            tickfont=dict(size=20),
        ),
        barmode='group',
    )
    if df_group_score.empty:
        fig_score.add_annotation(
            text='Não há dados suficientes',
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20)
        )
    graph_serie_nota.plotly_chart(fig_score, use_container_width=True)

    #endregion

    #region gráfico de barras da quantidade de series por faixa de episódios e a media de notas por faixa
    df_group_episodes = df_filtered.groupby('episode_range', as_index=False, observed=True)['series_title'].count()
    df_avg_score_by_episodes = df_filtered[df_filtered['my_score'] != 0].groupby('episode_range', as_index=False, observed=True)['my_score'].mean()

    fig_episode_range = go.Figure()
    fig_episode_range.add_trace(go.Bar(
        x=df_group_episodes['episode_range'],
        y=df_group_episodes['series_title'], 
        name='Quantidade de Animes',
    ))
    fig_episode_range.add_trace(go.Scatter(  
        x=df_avg_score_by_episodes['episode_range'], 
        y=df_avg_score_by_episodes['my_score'],
        mode='lines+markers', 
        name='Média de Nota',
        line=dict(color='red', width=2),
        yaxis='y2',
    ))

    fig_episode_range.update_layout(
        #titulo em h1
        title='Quantidade de Séries por Faixa de Episódios e média de notas',
        xaxis_title='Faixa de Episódios',
        yaxis_title='Quantidade de Séries',
        yaxis=dict(
            ticklabelposition='inside',
            tickfont=dict( size=20),
        ),
        yaxis2=dict(
            #titulo em h2
            title='Média de Nota',
            overlaying='y',
            side='right',
            range=[0,10],
            ticklabelposition='inside',
            tickfont=dict( color='Red', size=20),
        ),
        barmode='group',
    )
    if max(df_group_episodes['series_title']) == 0:
        fig_episode_range.add_annotation(
            text='Não há dados suficientes',
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20)
        )
    graph_serie_episodio_nota.plotly_chart(fig_episode_range, use_container_width=True)
    #endregion

    #region gráfico de pizza de quantidade de série por tipo
    df_series_by_type = df_filtered.groupby('series_type', observed=True)['series_title'].count()

    fig_series_by_type = px.pie(df_series_by_type, values='series_title', names=df_series_by_type.index, title='Quantidade de Séries por Tipo')

    if df_series_by_type.empty:
        #somente um texto dizendo que não ha dados o suficiente no meio do gráfico
        fig_series_by_type.add_annotation(
            text='Não há dados suficientes',
            showarrow=False,
            font=dict(size=20)
        )
    graph_series_tipo.plotly_chart(fig_series_by_type, use_container_width=True)
    #endregion

    #region timeline de quantidade de series assistidas por ano e média das notas por ano 
    df_series_by_year = df_filtered.groupby(df_filtered['my_finish_date'].dt.year, observed=True)['series_title'].count()
    df_avg_score_by_year = df_filtered[df_filtered['my_score'] != 0].groupby(df_filtered['my_finish_date'].dt.year)['my_score'].mean()

    fig_series_by_date = go.Figure()
    fig_series_by_date.add_trace(go.Scatter(
        x=df_series_by_year.index,       # O índice agora é o ano
        y=df_series_by_year.values,      # Os valores são as contagens de séries
        mode='lines+markers',            # Gráfico de linha com marcadores
        name='Quantidade de Séries'      # Nome da linha para a legenda
    ))
    fig_series_by_date.add_trace(go.Scatter(
        x=df_avg_score_by_year.index,    # O índice agora é o ano
        y=df_avg_score_by_year.values,   # Os valores são as médias de nota
        mode='lines+markers', 
        name='Média de Nota',
        line=dict(color='red', width=2),
        yaxis='y2'  # Associa ao eixo Y secundário
    ))

    fig_series_by_date.update_layout(
        title='Quantidade de Séries por Data de Conclusão',
        xaxis_title='Ano de Conclusão',
        yaxis_title='Quantidade de Séries',
        yaxis2=dict(
            title='Média de Nota',
            overlaying='y',
            side='right',
            range=[0,10]
        ),
    )
    if df_series_by_year.empty:
        fig_series_by_date.add_annotation(
            text='Não há dados suficientes',
            showarrow=False,
            font=dict(size=20)
        )
    graph_series_data_conclusao.plotly_chart(fig_series_by_date, use_container_width=True)
    #endregion

    #region gráfico donut de quantidade de series por status
    df_series_status = df_filtered.groupby('my_status', observed=True)['series_title'].count()
    fig_series_by_status = px.pie(
        df_series_status,
        values='series_title', 
        names=df_series_status.index, 
        title='Quantidade de Séries por Status',
        hole=0.5
    )
    if df_series_status.empty:
        fig_series_by_status.add_annotation(
            text='Não há dados suficientes',
            showarrow=False,
            font=dict(size=20)
        )
    graph_series_status.plotly_chart(fig_series_by_status, use_container_width=True)
    #endregion

    #region gráfico de barras de média de notas por tipo de série
    df_avg_score_by_type = df_filtered[df_filtered['my_score'] != 0].groupby('series_type', as_index=False, observed=True)['my_score'].mean()
    fig_date = px.bar(df_avg_score_by_type, x='series_type', y='my_score', title='Média de Nota por Tipo de Série')
    fig_date.update_layout(
        xaxis_title='Tipo de Série',
        yaxis_title='Média de Nota',
        yaxis=dict(range=[0,10]),
        
    )
    if df_avg_score_by_type.empty:
        #somente um texto dizendo que não ha dados o suficiente no meio do gráfico
        fig_date.add_annotation(
            text='Não há dados suficientes',
            showarrow=False,
            font=dict(size=20)
        )
    graph_nota_tipo.plotly_chart(fig_date, use_container_width=True)
    #endregion
    
    #region gráfico de barras do tempo gasto por nota e card 9 - tempo total gasto assistindo
    df_group_score = df_filtered.copy()
    df_group_score['time_spent'] = (df_filtered['num_episodes_watched'] * df_filtered['average_episode_duration']) / 3600
    df_group_score = df_group_score.groupby('my_score', as_index=False, observed=True)['time_spent'].sum()
    fig_score_by_time_spent = go.Figure()
    fig_score_by_time_spent.add_trace(go.Bar(
        x= df_group_score['my_score'],
        y= df_group_score['time_spent'],
        # name='Quantidade de Séries',
    ))

    fig_score_by_time_spent.update_layout(
        title='Tempo gasto em horas por Nota',
        xaxis_title='Nota',
        xaxis=dict(
            # range=[0,10],
            type='category',
        ),
        yaxis_title='tempo Gasto em horas',
        yaxis=dict(
            tickfont=dict(size=20),
        ),
        barmode='group',
    )
    if df_group_score.empty:
        fig_score_by_time_spent.add_annotation(
            text='Não há dados suficientes',
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20)
        )
    graph_tempo_nota.plotly_chart(fig_score_by_time_spent, use_container_width=True)
    card_tempo_gasto_total.metric("Tempo gasto assistindo", round(df_group_score['time_spent'].sum()/24, 2))

    #endregion

    #region gráfico donut de generos mais assistidos
    df_series_genre = df_filtered.explode('genres')
    df_series_genre = df_series_genre.groupby('genres', observed=True)['series_title'].count().sort_values(ascending=False).head(10)

    fig_series_by_genre = px.pie(
        df_series_genre,
        values='series_title', 
        names=df_series_genre.index, 
        title='Quantidade de Séries pelos 10 genero mais assistidos',
        hole=0.5
    )
    if df_series_genre.empty:
        fig_series_by_genre.add_annotation(
            text='Não há dados suficientes',
            showarrow=False,
            font=dict(size=20)
        )
    graph_series_genero.plotly_chart(fig_series_by_genre, use_container_width=True)
    #endregion

    #region Heatmap de completed por mês
    df_completion_month = df_filtered.copy()

    df_completion_month = df_completion_month.dropna(subset=['my_finish_date'])

    df_completion_month['YearMonth'] = df_completion_month['my_finish_date'].apply(
        lambda x: 'Sem data' if pd.isnull(x) else f"{x.year}-{x.month}"
    )
    df_completion_month['years'] = df_completion_month['my_finish_date'].apply(
        lambda x: x.year
    )
    df_completion_month['months'] = df_completion_month['my_finish_date'].apply(
        lambda x: 'Sem data' if pd.isnull(x) else calendar.month_name[x.month] 
    )

    df_completion_month = df_completion_month.groupby(['years', 'months'], observed=True).size().reset_index(name='completed_count')
    df_completion_month['years'] = df_completion_month['years'].astype(int)
    if not df_completion_month.empty:
        
        min_year = int(df_completion_month['years'].min())  
        max_year = int(df_completion_month['years'].max())  
        all_years = list(range(min_year, max_year + 1))  

        df_completion_month = (
            df_completion_month
            .set_index(['years', 'months'])
            .reindex([(year, month) for year in all_years for month in calendar.month_name[1:]], fill_value=0)
            .reset_index()
        )

    month_order = list(calendar.month_name[1:])

    heatmap = go.Figure(
        data=go.Heatmap(
            x=df_completion_month['years'], 
            y=pd.Categorical(df_completion_month['months'], categories=month_order, ordered=True), 
            z=df_completion_month['completed_count'], 
            colorscale='portland', #blues melhor até então - portland
        )
    )
    
    if df_completion_month.empty:
        heatmap.add_annotation(
            text='Não há dados suficientes',
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20)
        )
    else:
        heatmap.update_xaxes(
            title='Ano', 
            tickmode='array',  
            tickvals=all_years,  
            ticktext=[str(year) for year in all_years],  
            showgrid=True  
        )
        heatmap.update_yaxes(
            title='Mês', 
            categoryorder='array', 
            categoryarray=month_order
        )
    graph_heatmap.plotly_chart(heatmap, use_container_width=True)
    #endregion

    #region linha temporal - completed series
    df_completion_month = df_filtered.copy()
    df_completion_month = df_completion_month.dropna(subset=['my_finish_date'])
    unique_years = sorted(set(df_completion_month['my_finish_date'].dt.year))
    df_completion_month['YearMonth'] = df_completion_month['my_finish_date'].dt.to_period('M')
    df_completion_month = (
        df_completion_month.groupby('YearMonth', observed=True)
        .size()
        .reset_index(name='count')
    )
    df_completion_month = df_completion_month.sort_values('YearMonth')
    df_completion_month['cumulative_count'] = df_completion_month['count'].cumsum()
    df_completion_month['YearMonth'] = df_completion_month['YearMonth'].astype(str)

    fig_timeline = go.Figure()
    fig_timeline.add_trace(go.Scatter(
        x=df_completion_month['YearMonth'],
        y=df_completion_month['cumulative_count'],
        mode='lines+markers',
        name='Animes assistidos'
    ))
    fig_timeline.update_layout(
        title='Timeline de animes assistidos',
        xaxis_title='Mês/Ano',
        yaxis_title='Quantidade acumulada de animes',
        xaxis=dict(
            tickmode='array',
            tickvals= [f"{year}-01" for year in unique_years ],
            ticktext= [str(year) for year in unique_years ],
            tickangle=-45
        ),
        yaxis=dict(
            tickfont=dict(size=12),
        )
    )

    if month != "Mostrar todos":
        fig_timeline.add_annotation(
            text='Não há dados suficientes',
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20)
        )
    graph_timeline.plotly_chart(fig_timeline, use_container_width=True)
    #endregion
    st.header('Tabela de Animes')

    st.write(df_filtered)

