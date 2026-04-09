# Script para generar un informe HTML con gráficas basado en los datos de youtube_analytics.csv

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime
import argparse

def load_and_prepare_data(csv_file_path):
    # Carga y prepara los datos del CSV para graficar.
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"El archivo {csv_file_path} no se encontró. Ejecute main.py primero.")
    
    df = pd.read_csv(csv_file_path)
    
    # Convertir la columna 'Date' a tipo datetime para facilitar el filtrado y orden
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Ordenar por fecha para gráficos de series temporales
    df = df.sort_values(by='Date')
    
    print(f"Datos cargados. Total de registros: {len(df)}")
    print(f"Fechas disponibles: {df['Date'].min().date()} a {df['Date'].max().date()}")
    
    return df

def create_normal_videos_views_bar_chart(df):
    # Crea un gráfico de barras para vistas de videos normales por canal.
    # Filtrar y agrupar datos solo para videos normales
    df_normal = df[df['NORMAL_Views'] > 0]  # Solo canales con videos normales
    if df_normal.empty:
        # Si no hay datos, crear un DataFrame vacío con las columnas necesarias
        df_normal = pd.DataFrame(columns=['ChannelName', 'NORMAL_Views'])
    else:
        # Ordenar de mayor a menor según las vistas
        df_normal = df_normal.sort_values(by='NORMAL_Views', ascending=False)
    
    fig = px.bar(
        df_normal,
        x='ChannelName',
        y='NORMAL_Views',
        title="Vistas Totales de Videos Normales por Canal",
        labels={'NORMAL_Views': 'Número de Vistas'},
        color_discrete_sequence=['#636EFA']  # Azul para videos normales
    )
    
    fig.update_layout(
        xaxis_title="Canal",
        yaxis_title="Vistas Totales (Videos Normales)",
        height=600
    )
    return fig

def create_shorts_views_bar_chart(df):
    # Crea un gráfico de barras para vistas de Shorts por canal.
    # Filtrar y agrupar datos solo para Shorts
    df_shorts = df[df['SHORT_Views'] > 0]  # Solo canales con Shorts
    if df_shorts.empty:
        # Si no hay datos, crear un DataFrame vacío con las columnas necesarias
        df_shorts = pd.DataFrame(columns=['ChannelName', 'SHORT_Views'])
    else:
        # Ordenar de mayor a menor según las vistas
        df_shorts = df_shorts.sort_values(by='SHORT_Views', ascending=False)
    
    fig = px.bar(
        df_shorts,
        x='ChannelName',
        y='SHORT_Views',
        title="Vistas Totales de Shorts por Canal",
        labels={'SHORT_Views': 'Número de Vistas'},
        color_discrete_sequence=['#EF553B']  # Rojo para Shorts
    )
    
    fig.update_layout(
        xaxis_title="Canal",
        yaxis_title="Vistas Totales (Shorts)",
        height=600
    )
    return fig

def create_live_views_bar_chart(df):
    # Crea un gráfico de barras para vistas de videos en vivo por canal.
    # Filtrar y agrupar datos solo para videos en vivo
    df_live = df[df['LIVE_Views'] > 0]  # Solo canales con videos en vivo
    if df_live.empty:
        # Si no hay datos, crear un DataFrame vacío con las columnas necesarias
        df_live = pd.DataFrame(columns=['ChannelName', 'LIVE_Views'])
    else:
        # Ordenar de mayor a menor según las vistas
        df_live = df_live.sort_values(by='LIVE_Views', ascending=False)
    
    fig = px.bar(
        df_live,
        x='ChannelName',
        y='LIVE_Views',
        title="Vistas Totales de Videos En Vivo por Canal",
        labels={'LIVE_Views': 'Número de Vistas'},
        color_discrete_sequence=['#00CC96']  # Verde para videos en vivo
    )
    
    fig.update_layout(
        xaxis_title="Canal",
        yaxis_title="Vistas Totales (En Vivo)",
        height=600
    )
    return fig

def create_normal_videos_avg_views_bar_chart(df):
    # Crea un gráfico de barras para promedio de vistas por video normal por canal.
    # Filtrar y agrupar datos solo para videos normales
    df_normal = df[df['NORMAL_Count'] > 0]  # Solo canales con videos normales
    if df_normal.empty:
        # Si no hay datos, crear un DataFrame vacío con las columnas necesarias
        df_normal = pd.DataFrame(columns=['ChannelName', 'NORMAL_Avg_Views_Per_Video'])
    else:
        # Ordenar de mayor a menor según el promedio de vistas
        df_normal = df_normal.sort_values(by='NORMAL_Avg_Views_Per_Video', ascending=False)
    
    fig = px.bar(
        df_normal,
        x='ChannelName',
        y='NORMAL_Avg_Views_Per_Video',
        title="Promedio de Vistas por Video Normal por Canal",
        labels={'NORMAL_Avg_Views_Per_Video': 'Promedio de Vistas por Video'},
        color_discrete_sequence=['#636EFA']  # Azul para videos normales
    )
    
    fig.update_layout(
        xaxis_title="Canal",
        yaxis_title="Promedio de Vistas por Video Normal",
        height=600
    )
    return fig

def create_shorts_avg_views_bar_chart(df):
    # Crea un gráfico de barras para promedio de vistas por Short por canal.
    # Filtrar y agrupar datos solo para Shorts
    df_shorts = df[df['SHORT_Count'] > 0]  # Solo canales con Shorts
    if df_shorts.empty:
        # Si no hay datos, crear un DataFrame vacío con las columnas necesarias
        df_shorts = pd.DataFrame(columns=['ChannelName', 'SHORT_Avg_Views_Per_Video'])
    else:
        # Ordenar de mayor a menor según el promedio de vistas
        df_shorts = df_shorts.sort_values(by='SHORT_Avg_Views_Per_Video', ascending=False)
    
    fig = px.bar(
        df_shorts,
        x='ChannelName',
        y='SHORT_Avg_Views_Per_Video',
        title="Promedio de Vistas por Short por Canal",
        labels={'SHORT_Avg_Views_Per_Video': 'Promedio de Vistas por Short'},
        color_discrete_sequence=['#EF553B']  # Rojo para Shorts
    )
    
    fig.update_layout(
        xaxis_title="Canal",
        yaxis_title="Promedio de Vistas por Short",
        height=600
    )
    return fig

def create_live_avg_views_bar_chart(df):
    # Crea un gráfico de barras para promedio de vistas por video en vivo por canal.
    # Filtrar y agrupar datos solo para videos en vivo
    df_live = df[df['LIVE_Count'] > 0]  # Solo canales con videos en vivo
    if df_live.empty:
        # Si no hay datos, crear un DataFrame vacío con las columnas necesarias
        df_live = pd.DataFrame(columns=['ChannelName', 'LIVE_Avg_Views_Per_Video'])
    else:
        # Ordenar de mayor a menor según el promedio de vistas
        df_live = df_live.sort_values(by='LIVE_Avg_Views_Per_Video', ascending=False)
    
    fig = px.bar(
        df_live,
        x='ChannelName',
        y='LIVE_Avg_Views_Per_Video',
        title="Promedio de Vistas por Video En Vivo por Canal",
        labels={'LIVE_Avg_Views_Per_Video': 'Promedio de Vistas por Video'},
        color_discrete_sequence=['#00CC96']  # Verde para videos en vivo
    )
    
    fig.update_layout(
        xaxis_title="Canal",
        yaxis_title="Promedio de Vistas por Video En Vivo",
        height=600
    )
    return fig

def generate_html_report(figures, output_file):
    # Genera un archivo HTML que contiene todas las figuras.
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE html>\n")
        f.write("<html>\n<head>\n")
        f.write("<title>Informe de Analítica de YouTube</title>\n")
        f.write("<style>\n")
        f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
        f.write("h1, h2 { color: #333; }\n")
        f.write(".chart-container { margin-bottom: 40px; }\n")
        f.write("</style>\n")
        f.write("</head>\n<body>\n")
        f.write(f"<h1>Informe de Analítica de YouTube - Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>\n")
        
        # Cargar Plotly.js al inicio
        f.write("<script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script>\n")
        
        for i, (title, fig) in enumerate(figures):
            f.write(f"<div class='chart-container'>\n")
            f.write(f"<h2>{title}</h2>\n")
            # Convertir la figura directamente a HTML
            fig_html = fig.to_html(include_plotlyjs=False, full_html=False)
            f.write(fig_html)
            f.write("</div>\n")
        
        f.write("</body>\n</html>\n")
    
    print(f"Informe HTML generado: {output_file}")

def main():
    # Función principal para ejecutar el script.
    parser = argparse.ArgumentParser(description='Genera un informe HTML con gráficas a partir de datos de YouTube Analytics.')
    parser.add_argument('--csv', default='youtube_analytics_90D.csv', help='Ruta al archivo CSV de entrada.')
    parser.add_argument('--output', default='youtube_analytics_report.html', help='Ruta al archivo HTML de salida.')
    args = parser.parse_args()

    print("Cargando datos...")
    df = load_and_prepare_data(args.csv)
    
    if df.empty:
        print("No hay datos para generar el informe.")
        return

    print("Creando gráficos...")
    figures = []
    
    # Nuevas gráficas específicas
    try:
        fig1 = create_normal_videos_views_bar_chart(df)
        figures.append(("Vistas Totales de Videos Normales por Canal", fig1))
    except Exception as e:
        print(f"Error al crear el gráfico de vistas de videos normales: {e}")

    try:
        fig2 = create_shorts_views_bar_chart(df)
        figures.append(("Vistas Totales de Shorts por Canal", fig2))
    except Exception as e:
        print(f"Error al crear el gráfico de vistas de Shorts: {e}")

    try:
        fig3 = create_live_views_bar_chart(df)
        figures.append(("Vistas Totales de Videos En Vivo por Canal", fig3))
    except Exception as e:
        print(f"Error al crear el gráfico de vistas de videos en vivo: {e}")
        
    # Nuevas gráficas de promedio de vistas por video
    try:
        fig4 = create_normal_videos_avg_views_bar_chart(df)
        figures.append(("Promedio de Vistas por Video Normal por Canal", fig4))
    except Exception as e:
        print(f"Error al crear el gráfico de promedio de vistas por video normal: {e}")

    try:
        fig5 = create_shorts_avg_views_bar_chart(df)
        figures.append(("Promedio de Vistas por Short por Canal", fig5))
    except Exception as e:
        print(f"Error al crear el gráfico de promedio de vistas por Short: {e}")

    try:
        fig6 = create_live_avg_views_bar_chart(df)
        figures.append(("Promedio de Vistas por Video En Vivo por Canal", fig6))
    except Exception as e:
        print(f"Error al crear el gráfico de promedio de vistas por video en vivo: {e}")

    if not figures:
        print("No se pudieron crear gráficos.")
        return
        
    print("Generando informe HTML...")
    generate_html_report(figures, args.output)
    print("¡Informe generado con éxito!")

if __name__ == "__main__":
    main()