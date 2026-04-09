import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

# --- CONFIGURACIÓN CARGADA DESDE .env ---
YT_API_KEY = os.getenv("YT_API")
YT_CHANNEL_MAP_STR = os.getenv("YT_CHANNEL_MAP", "")
YT_DAYS_TO_ANALYZE = int(os.getenv("YT_DAYS_TO_ANALYZE", 1))

CSV_FILE = f'youtube_analytics_{YT_DAYS_TO_ANALYZE}D.csv'

def get_video_ids_from_playlist(youtube, playlist_id, start_date):
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
                break
            else:
                raise e
    return video_ids

def fetch_playlist_video_ids_task(playlist_id, start_date, channel_name, video_type):
    """
    Tarea ejecutada por un hilo para obtener video IDs de una playlist.
    Crea su propia instancia del cliente de YouTube para evitar problemas de concurrencia.
    """
    try:
        # Crear una nueva instancia del cliente para este hilo
        youtube = build('youtube', 'v3', developerKey=YT_API_KEY)
        video_ids = get_video_ids_from_playlist(youtube, playlist_id, start_date)
        return {
            'status': 'success',
            'channel_name': channel_name,
            'video_type': video_type,
            'playlist_id': playlist_id,
            'video_ids': video_ids
        }
    except Exception as e:
        return {
            'status': 'error',
            'channel_name': channel_name,
            'video_type': video_type,
            'playlist_id': playlist_id,
            'error': str(e)
        }

def parse_channel_map(map_string):
    """Parsea la cadena de mapeo de canales desde la variable de entorno."""
    channel_map = {}
    if not map_string:
        return channel_map
    
    entries = map_string.split(',')
    for entry in entries:
        parts = entry.split(':')
        if len(parts) == 2:
            name = parts[0].strip()
            channel_id = parts[1].strip()
            channel_map[name] = channel_id
    return channel_map

def fetch_all_video_stats(youtube, video_id_details):
    """
    Obtiene las estadísticas para una lista de videos en lotes.
    Args:
        youtube: El objeto de servicio de la API de YouTube.
        video_id_details: Lista de diccionarios con claves 'id', 'channel_name', 'video_type'.
    Returns:
        dict: Un diccionario con estadísticas por canal y tipo de video.
              Formato: { (channel_name, video_type): {'view_count': int, 'video_count': int} }
    """
    if not video_id_details:
        return {}

    # Preparar un diccionario para acumular resultados
    stats_dict = {}
    # Diccionario auxiliar para contar videos por canal y tipo
    video_count_dict = {}

    # Extraer todos los IDs de video
    all_video_ids = [item['id'] for item in video_id_details]
    
    print(f"Obteniendo estadísticas para {len(all_video_ids)} videos en lotes de 50...")
    
    # Procesar los IDs en lotes de 50
    for i in range(0, len(all_video_ids), 50):
        chunk_ids = all_video_ids[i:i+50]
        try:
            videos_request = youtube.videos().list(
                part="statistics",
                id=",".join(chunk_ids)
            )
            videos_response = videos_request.execute()
            
            # Crear un conjunto de IDs procesados en esta respuesta para verificar
            processed_ids_in_chunk = set()
            
            for item in videos_response.get("items", []):
                video_id = item['id']
                view_count = int(item['statistics'].get('viewCount', 0))
                processed_ids_in_chunk.add(video_id)
                
                # Encontrar el detalle original para este video_id
                original_detail = next((detail for detail in video_id_details if detail['id'] == video_id), None)
                if original_detail:
                    channel_name = original_detail['channel_name']
                    video_type = original_detail['video_type']
                    key = (channel_name, video_type)
                    
                    if key not in stats_dict:
                        stats_dict[key] = {'view_count': 0, 'video_count': 0}
                    
                    stats_dict[key]['view_count'] += view_count
            
            # Actualizar el conteo de videos para las entradas procesadas en este chunk
            for detail in video_id_details:
                if detail['id'] in processed_ids_in_chunk:
                    key = (detail['channel_name'], detail['video_type'])
                    if key not in video_count_dict:
                        video_count_dict[key] = 0
                    video_count_dict[key] += 1
                        
        except Exception as e:
            print(f"Error al obtener estadísticas para un lote de videos: {e}")
            # Podríamos decidir continuar o detenernos. Por ahora, continuamos.
    
    # Combinar el conteo de videos con las estadísticas
    for key, count in video_count_dict.items():
        if key in stats_dict:
            stats_dict[key]['video_count'] = count
        else:
            # En caso de que un video no tenga estadísticas (raro, pero posible)
            stats_dict[key] = {'view_count': 0, 'video_count': count}
            
    return stats_dict

def main():
    channel_map = parse_channel_map(YT_CHANNEL_MAP_STR)

    if not channel_map:
        print("La variable de entorno YT_CHANNEL_MAP no está configurada o tiene un formato incorrecto.")
        return

    start_date = datetime.now(timezone.utc) - timedelta(days=YT_DAYS_TO_ANALYZE)
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    # Lista para almacenar temporalmente todos los video_ids con su metadata
    all_video_id_details = []
    
    # --- Primera pasada: recolectar todos los video_ids de todas las playlists (CONCURRENTE) ---
    
    # Preparar lista de tareas
    tasks = []
    for channel_name, channel_id in channel_map.items():
        print(f"--- Preparando análisis para el Canal: {channel_name} ({channel_id}) ---")
        
        if not channel_id.startswith("UC"):
            print(f"ID de canal no válido para '{channel_name}': {channel_id}. Saltando...")
            continue

        playlist_id_suffix = channel_id[2:]
        playlists = {
            "NORMAL": f"UULF{playlist_id_suffix}",
            "SHORT": f"UUSH{playlist_id_suffix}",
            "LIVE": f"UULV{playlist_id_suffix}"
        }

        day_str = "día" if YT_DAYS_TO_ANALYZE == 1 else "días"
        print(f"Preparando recopilación de videos de los últimos {YT_DAYS_TO_ANALYZE} {day_str} para el canal: {channel_name}")

        for video_type, playlist_id in playlists.items():
             # Añadir tarea a la lista
            tasks.append((playlist_id, start_date, channel_name, video_type))
    
    if not tasks:
        print("No se encontraron tareas para ejecutar.")
        return
        
    print(f"\nIniciando recopilación concurrente para {len(tasks)} playlists...")
    
    # Determinar número de workers (hilos)
    # Un buen punto de partida: min(32, número_de_tareas + 4)
    max_workers = min(32, len(tasks) + 4)
    
    # Ejecutar tareas concurrentemente
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todas las tareas al executor
        future_to_task = {executor.submit(fetch_playlist_video_ids_task, *task): task for task in tasks}
        
        # Recoger resultados a medida que se completan
        for future in as_completed(future_to_task):
            task_info = future_to_task[future]
            channel_name, video_type = task_info[2], task_info[3]
            try:
                result = future.result()
                if result['status'] == 'success':
                    video_ids = result['video_ids']
                    print(f"  - [{channel_name}][{video_type}S] {len(video_ids)} videos encontrados")
                    # Almacenar los detalles de cada video_id
                    for video_id in video_ids:
                        all_video_id_details.append({
                            'id': video_id,
                            'channel_name': result['channel_name'],
                            'video_type': result['video_type']
                        })
                else:
                    error_msg = result['error']
                    if "playlistNotFound" in error_msg:
                        print(f"  - [{channel_name}][{video_type}S] 0 videos - Playlist no encontrada")
                    else:
                        print(f"  - [{channel_name}][{video_type}S] Error: {error_msg}")
            except Exception as exc:
                print(f'  - [{channel_name}][{video_type}S] Generó una excepción: {exc}')
    
    # --- Fin de la recopilación concurrente ---
    
    if not all_video_id_details:
        print("No se encontraron videos para analizar.")
        return

    print(f"\nTotal de videos recopilados: {len(all_video_id_details)}")
    
    # Segunda pasada: obtener todas las estadísticas en una sola operación agrupada
    # Creamos una instancia de youtube para esta parte, ya que es segura y no concurrente.
    youtube = build('youtube', 'v3', developerKey=YT_API_KEY)
    all_stats = fetch_all_video_stats(youtube, all_video_id_details)
    
    # Tercera pasada: construir la estructura de datos final por canal
    all_channels_data = []
    for channel_name in channel_map.keys():
        channel_data = {'Date': today_date, 'ChannelName': channel_name}
        for video_type in ["NORMAL", "SHORT", "LIVE"]:
            key = (channel_name, video_type)
            stats = all_stats.get(key, {'view_count': 0, 'video_count': 0})
            count = stats['video_count']
            views = stats['view_count']
            channel_data[f'{video_type}_Count'] = count
            channel_data[f'{video_type}_Views'] = views
            # Calcular el promedio de vistas por video, evitando división por cero
            if count > 0:
                channel_data[f'{video_type}_Avg_Views_Per_Video'] = round(views / count, 2)
            else:
                channel_data[f'{video_type}_Avg_Views_Per_Video'] = 0
        all_channels_data.append(channel_data)
    
    # Imprimir resumen por canal
    print("\n--- Resumen de Análisis ---")
    for data in all_channels_data:
        print(f"\nCanal: {data['ChannelName']}")
        print(f"  Normales: {data['NORMAL_Count']} (Vistas: {data['NORMAL_Views']:,}) (Promedio: {data['NORMAL_Avg_Views_Per_Video']:,})")
        print(f"  Shorts: {data['SHORT_Count']} (Vistas: {data['SHORT_Views']:,}) (Promedio: {data['SHORT_Avg_Views_Per_Video']:,})")
        print(f"  En Vivo: {data['LIVE_Count']} (Vistas: {data['LIVE_Views']:,}) (Promedio: {data['LIVE_Avg_Views_Per_Video']:,})")
        print("-" * 30)

    if not all_channels_data:
        print("No se recolectaron datos para guardar.")
        return

    df = pd.DataFrame(all_channels_data)
    column_order = [
        'Date', 'ChannelName',
        'NORMAL_Count', 'NORMAL_Views', 'NORMAL_Avg_Views_Per_Video',
        'SHORT_Count', 'SHORT_Views', 'SHORT_Avg_Views_Per_Video',
        'LIVE_Count', 'LIVE_Views', 'LIVE_Avg_Views_Per_Video'
    ]
    df = df.reindex(columns=column_order) # Use reindex to avoid errors if a column is missing

    file_exists = os.path.exists(CSV_FILE)
    df.to_csv(CSV_FILE, mode='a', header=not file_exists, index=False)

    print(f"\n¡Éxito! Todos los datos han sido guardados en '{CSV_FILE}'")

if __name__ == "__main__":
    main()
