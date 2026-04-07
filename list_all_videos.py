import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone

load_dotenv()

# --- CONFIGURACIÓN CARGADA DESDE .env ---
YT_API_KEY = os.getenv("YT_API")
YT_CHANNEL_MAP_STR = os.getenv("YT_CHANNEL_MAP", "")
# Usar 7 días como valor predeterminado, igual que top_video_report.py
YT_DAYS_TO_ANALYZE = int(os.getenv("YT_DAYS_TO_ANALYZE", 7))

CSV_OUTPUT_FILE = 'all_videos_report.csv'

def parse_channel_map(map_string):
    """Parsea la cadena de mapeo de canales desde la variable de entorno."""
    channel_map = {}
    if not map_string:
        print("Advertencia: YT_CHANNEL_MAP no está definido o está vacío.")
        return channel_map
    
    entries = map_string.split(',')
    for entry in entries:
        parts = entry.split(':')
        if len(parts) == 2:
            name = parts[0].strip()
            channel_id = parts[1].strip()
            channel_map[name] = channel_id
        else:
             print(f"Advertencia: Entrada de canal no válida, se omite: '{entry}'")
    return channel_map

def get_all_video_ids_from_playlist(youtube, playlist_id, start_date):
    """Obtiene una lista de video IDs de una playlist, filtrados por fecha."""
    video_ids = []
    next_page_token = None
    while True:
        try:
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            for item in response.get("items", []):
                published_at_str = item['snippet']['publishedAt']
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                if published_at >= start_date:
                    video_ids.append(item['snippet']['resourceId']['videoId'])
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        except Exception as e:
            if "playlistNotFound" in str(e):
                print(f"  - Lista de reproducción no encontrada: {playlist_id}")
                break
            else:
                print(f"  - Error al obtener elementos de la lista {playlist_id}: {e}")
                break
    return video_ids

def get_video_details_in_batches(youtube, video_ids, channel_name, video_type):
    """
    Obtiene los detalles de una lista de video IDs en lotes.
    Args:
        youtube: El objeto de servicio de la API de YouTube.
        video_ids: Lista de IDs de video.
        channel_name: Nombre del canal.
        video_type: Tipo de video (NORMAL, SHORT, LIVE).
    Returns:
        list: Lista de diccionarios con los detalles de los videos.
    """
    video_details = []
    
    if not video_ids:
        return video_details

    print(f"Obteniendo detalles para {len(video_ids)} videos de tipo {video_type}...")
    
    # Procesar los IDs en lotes de 50
    for i in range(0, len(video_ids), 50):
        chunk_ids = video_ids[i:i+50]
        try:
            videos_request = youtube.videos().list(
                part="snippet,statistics",
                id=",".join(chunk_ids)
            )
            videos_response = videos_request.execute()
            
            for item in videos_response.get("items", []):
                video_id = item['id']
                title = item['snippet']['title']
                view_count = int(item['statistics'].get('viewCount', 0))
                like_count = int(item['statistics'].get('likeCount', 0))
                published_at_str = item['snippet']['publishedAt']
                
                video_details.append({
                    'Date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                    'ChannelName': channel_name,
                    'VideoType': video_type,
                    'VideoID': video_id,
                    'Title': title,
                    'ViewCount': view_count,
                    'LikeCount': like_count,
                    'PublishedAt': published_at_str
                })
                    
        except Exception as e:
            print(f"Error al obtener detalles para un lote de videos: {e}")
            # Continuar con el siguiente lote
            
    return video_details

def main():
    print("--- Iniciando Generación de Reporte Detallado de Todos los Videos ---")
    channel_map = parse_channel_map(YT_CHANNEL_MAP_STR)

    if not channel_map:
        print("Error: La variable de entorno YT_CHANNEL_MAP no está configurada o tiene un formato incorrecto.")
        return

    # Calcular la fecha de inicio para el filtro
    start_date = datetime.now(timezone.utc) - timedelta(days=YT_DAYS_TO_ANALYZE)
    start_date_iso = start_date.isoformat().replace('+00:00', 'Z') # Formato requerido por la API
    
    day_str = "día" if YT_DAYS_TO_ANALYZE == 1 else "días"
    print(f"Buscando todos los videos de los últimos {YT_DAYS_TO_ANALYZE} {day_str}...")

    youtube = build('youtube', 'v3', developerKey=YT_API_KEY)
    
    all_videos_data = []

    for channel_name, channel_id in channel_map.items():
        print(f"\n--- Analizando Canal: {channel_name} ({channel_id}) ---")
        
        if not channel_id.startswith("UC"):
            print(f"ID de canal no válido para '{channel_name}': {channel_id}. Saltando...")
            continue

        playlist_id_suffix = channel_id[2:]
        playlists = {
            "NORMAL": f"UULF{playlist_id_suffix}",
            "SHORT": f"UUSH{playlist_id_suffix}",
            "LIVE": f"UULV{playlist_id_suffix}"
        }

        for video_type, playlist_id in playlists.items():
            print(f"  - Buscando en lista '{video_type}' ({playlist_id})...")
            
            # 1. Obtener todos los video IDs de la playlist filtrados por fecha
            video_ids = get_all_video_ids_from_playlist(youtube, playlist_id, start_date)
            
            if not video_ids:
                print(f"    - No se encontraron videos en esta lista en el periodo especificado.")
                continue
            
            print(f"    - Encontrados {len(video_ids)} videos.")
            
            # 2. Obtener detalles de todos esos videos
            video_details = get_video_details_in_batches(youtube, video_ids, channel_name, video_type)
            all_videos_data.extend(video_details)

    if not all_videos_data:
        print("\nNo se encontraron videos para ningún canal.")
        # Crear un CSV vacío con encabezados
        df_empty = pd.DataFrame(columns=[
            'Date', 'ChannelName', 'VideoType', 'VideoID', 'Title',
            'ViewCount', 'LikeCount', 'PublishedAt'
        ])
        df_empty.to_csv(CSV_OUTPUT_FILE, index=False)
        print(f"Se ha creado un archivo CSV vacío: '{CSV_OUTPUT_FILE}'")
        return

    # Crear DataFrame y guardar en CSV
    df = pd.DataFrame(all_videos_data)
    # Reordenar columnas para claridad
    column_order = [
        'Date', 'ChannelName', 'VideoType', 'VideoID', 'Title',
        'ViewCount', 'LikeCount', 'PublishedAt'
    ]
    df = df.reindex(columns=column_order)
    
    df.to_csv(CSV_OUTPUT_FILE, index=False)
    print(f"\n¡Éxito! Reporte detallado de todos los videos guardado en '{CSV_OUTPUT_FILE}'")


if __name__ == "__main__":
    main()