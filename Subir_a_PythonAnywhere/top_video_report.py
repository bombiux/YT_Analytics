import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import argparse

load_dotenv()

# --- CONFIGURACIÓN CARGADA DESDE .env ---
YT_API_KEY = os.getenv("YT_API")
YT_CHANNEL_MAP_STR = os.getenv("YT_CHANNEL_MAP", "")
YT_DAYS_TO_ANALYZE = int(os.getenv("YT_DAYS_TO_ANALYZE", 7)) # Default to 7 days if not set

CSV_OUTPUT_FILE = 'top_videos_report.csv'

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

def get_top_video_from_playlist(youtube, playlist_id, start_date_iso):
    """
    Obtiene el video con más vistas de una playlist, filtrado por fecha.
    Args:
        youtube: El objeto de servicio de la API de YouTube.
        playlist_id: ID de la lista de reproducción.
        start_date_iso: Fecha de inicio en formato ISO 8601 para `publishedAfter`.
    Returns:
        dict: Diccionario con la información del video, o None si no se encuentra.
    """
    try:
        # La API permite ordenar por viewCount en orden descendente
        # y filtrar por fecha de publicación.
        request = youtube.playlistItems().list(
            part="snippet,contentDetails", # contentDetails incluye videoId
            playlistId=playlist_id,
            maxResults=50, # Obtenemos un lote para empezar
            orderBy="viewCount", # Orden descendente por vistas
            publishedAfter=start_date_iso
        )
        response = request.execute()
        
        video_items = response.get("items", [])
        if not video_items:
             # print(f"  - No se encontraron videos en la lista {playlist_id} desde {start_date_iso}.")
             return None

        # Extraer IDs de video del primer lote
        video_ids = [item['contentDetails']['videoId'] for item in video_items]
        
        # Obtener estadísticas para este primer lote de videos
        videos_request = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids)
        )
        videos_response = videos_request.execute()
        
        # Buscar el video con más vistas en este primer lote
        top_video = None
        max_views = -1
        for item in videos_response.get("items", []):
            # Asegurarse de que la fecha de publicación sea válida (aunque publishedAfter debería filtrar)
            published_at_str = item['snippet']['publishedAt']
            published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
            if published_at >= datetime.fromisoformat(start_date_iso.replace('Z', '+00:00')):
                view_count = int(item['statistics'].get('viewCount', 0))
                if view_count > max_views:
                    max_views = view_count
                    top_video = item
        
        if top_video:
            return top_video
        else:
             # print(f"  - No se encontró un video válido en el primer lote de la lista {playlist_id}.")
             # Si el primer lote no tiene videos válidos, podríamos paginar.
             # Sin embargo, para encontrar el "top" video, el primer lote ordenado suele ser suficiente.
             # La API de YouTube PlaylistItems.list no permite ordenar directamente por estadísticas,
             # solo por fecha o posición. El parámetro `orderBy` no existe para `playlistItems.list`.
             # Por lo tanto, debemos obtener los IDs y luego consultar `videos.list`.
             # El enfoque será:
             # 1. Obtener todos los video IDs de la playlist (filtrados por fecha).
             # 2. Obtener estadísticas de todos esos videos en lotes.
             # 3. Encontrar el que tenga más vistas.
             
             # Vamos a reimplementar esta función correctamente.
            return None
            
    except Exception as e:
        print(f"Error al obtener videos de la lista {playlist_id}: {e}")
        return None

def get_all_video_ids_from_playlist(youtube, playlist_id, start_date, end_date):
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
                if start_date <= published_at <= end_date:
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

def find_top_video_by_stats(youtube, video_ids):
    """
    Encuentra el video con más vistas de una lista de IDs.
    Args:
        youtube: El objeto de servicio de la API de YouTube.
        video_ids: Lista de IDs de video.
    Returns:
        dict: El objeto de video con más vistas, o None.
    """
    if not video_ids:
        return None

    max_views = -1
    top_video = None
    # print(f"Obteniendo estadísticas para {len(video_ids)} videos en lotes de 50...")
    
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
                 view_count = int(item['statistics'].get('viewCount', 0))
                 if view_count > max_views:
                    max_views = view_count
                    top_video = item
                        
        except Exception as e:
            print(f"Error al obtener estadísticas para un lote de videos: {e}")
            # Continuar con el siguiente lote
            
    return top_video

def main():
    parser = argparse.ArgumentParser(description="Genera reporte de top videos de YouTube en un rango de fechas.")
    parser.add_argument('--start', type=str, help="Fecha de inicio (DD/MM/YYYY)")
    parser.add_argument('--end', type=str, help="Fecha de fin (DD/MM/YYYY)")
    args = parser.parse_args()

    print("--- Iniciando Generación de Reporte de Videos Destacados ---")
    channel_map = parse_channel_map(YT_CHANNEL_MAP_STR)

    if not channel_map:
        print("Error: La variable de entorno YT_CHANNEL_MAP no está configurada o tiene un formato incorrecto.")
        return

    # Calcular fechas
    if args.start and args.end:
        try:
            start_date = datetime.strptime(args.start, "%d/%m/%Y").replace(tzinfo=timezone.utc)
            end_date = datetime.strptime(args.end, "%d/%m/%Y").replace(tzinfo=timezone.utc) + timedelta(days=1, microseconds=-1)
            print(f"Rango de búsqueda: {args.start} al {args.end}")
        except ValueError:
            print("Error: Formato de fecha incorrecto. Use DD/MM/YYYY (ej. 23/02/2026).")
            return
    else:
        # Fallback usando las variables de entorno
        start_date = datetime.now(timezone.utc) - timedelta(days=YT_DAYS_TO_ANALYZE)
        end_date = datetime.now(timezone.utc)
        day_str = "día" if YT_DAYS_TO_ANALYZE == 1 else "días"
        print(f"Buscando videos destacados de los últimos {YT_DAYS_TO_ANALYZE} {day_str}...")

    youtube = build('youtube', 'v3', developerKey=YT_API_KEY)
    
    top_videos_data = []

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
            video_ids = get_all_video_ids_from_playlist(youtube, playlist_id, start_date, end_date)
            
            if not video_ids:
                print(f"    - No se encontraron videos en esta lista en el periodo especificado.")
                continue
            
            # print(f"    - Encontrados {len(video_ids)} videos. Buscando el de más vistas...")
            
            # 2. Encontrar el video con más vistas entre esos IDs
            top_video = find_top_video_by_stats(youtube, video_ids)
            
            if top_video:
                title = top_video['snippet']['title']
                video_id = top_video['id']
                view_count = int(top_video['statistics'].get('viewCount', 0))
                like_count = int(top_video['statistics'].get('likeCount', 0))
                published_at_str = top_video['snippet']['publishedAt']
                
                print(f"    - Video destacado encontrado: '{title}' (ID: {video_id})")
                
                top_videos_data.append({
                    'Date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                    'ChannelName': channel_name,
                    'VideoType': video_type,
                    'VideoID': video_id,
                    'Title': title,
                    'ViewCount': view_count,
                    'LikeCount': like_count,
                    'PublishedAt': published_at_str
                })
            else:
                print(f"    - No se pudo determinar un video destacado para esta lista.")

    if not top_videos_data:
        print("\nNo se encontraron videos destacados para ningún canal.")
        # Crear un CSV vacío con encabezados
        df_empty = pd.DataFrame(columns=[
            'Date', 'ChannelName', 'VideoType', 'VideoID', 'Title',
            'ViewCount', 'LikeCount', 'PublishedAt'
        ])
        df_empty.to_csv(CSV_OUTPUT_FILE, index=False)
        print(f"Se ha creado un archivo CSV vacío: '{CSV_OUTPUT_FILE}'")
        return

    # Crear DataFrame y guardar en CSV
    df = pd.DataFrame(top_videos_data)
    # Reordenar columnas para claridad
    column_order = [
        'Date', 'ChannelName', 'VideoType', 'VideoID', 'Title',
        'ViewCount', 'LikeCount', 'PublishedAt'
    ]
    df = df.reindex(columns=column_order)
    
    df.to_csv(CSV_OUTPUT_FILE, index=False)
    print(f"\n¡Éxito! Reporte de videos destacados guardado en '{CSV_OUTPUT_FILE}'")


if __name__ == "__main__":
    main()