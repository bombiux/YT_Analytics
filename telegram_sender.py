import os
import requests
from dotenv import load_dotenv

def send_telegram_message(bot_token, chat_id, message):
    """
    Envía un mensaje de Telegram a través de la API oficial.
    """
    if not bot_token or not chat_id:
        print(f"Faltan credenciales (Bot Token o Chat ID) para {chat_id}.")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"[OK] Mensaje enviado por Telegram al chat {chat_id}.")
            return True
        else:
            print(f"[ERROR] No se pudo enviar a {chat_id}. HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Excepción al enviar mensaje de Telegram: {e}")
        return False

def send_telegram_document(bot_token, chat_id, document_path):
    """
    Envía un documento por Telegram.
    """
    if not bot_token or not chat_id or not os.path.exists(document_path):
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    try:
        with open(document_path, 'rb') as doc:
            files = {'document': doc}
            data = {'chat_id': chat_id}
            response = requests.post(url, data=data, files=files)
            if response.status_code == 200:
                print(f"[OK] Documento enviado por Telegram al chat {chat_id}.")
                return True
            else:
                print(f"[ERROR] No se pudo enviar documento a {chat_id}. HTTP: {response.status_code}")
                return False
    except Exception as e:
        print(f"[ERROR] Excepción al enviar documento de Telegram: {e}")
        return False


def format_and_send_reports(top_videos_by_channel):
    """
    Formatea el diccionario del Top 5 y lo envía a los chats de Telegram.
    """
    load_dotenv()
    
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat_1 = os.getenv("TELEGRAM_CHAT_ID_1", "").strip()
    tg_chat_2 = os.getenv("TELEGRAM_CHAT_ID_2", "").strip()
    
    if not top_videos_by_channel:
        print("No hay datos en el reporte para mandar por Telegram.")
        return

    # Usamos formato HTML soportado por Telegram
    lines = ["📊 <b>REPORTE TOP 5 VIDEOS POR CANAL</b> 📊\n"]
    
    for channel, videos in top_videos_by_channel.items():
        lines.append(f"📺 <b>Canal:</b> {channel}")
        for _, row in videos.iterrows():
            title = row['Title']
            views = int(row['ViewCount'])
            v_type = row['VideoType']
            video_id = row['VideoID']
            
            # Limitar título largo para legibilidad
            if len(title) > 65:
                title = title[:62] + "..."
            
            # Escapar caracteres de HTML básico para no romper la API de telegram si el título usa <>
            title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # Envolver el título en un enlace clickeable hacia YouTube
            url = f"https://youtu.be/{video_id}"
            lines.append(f"• [{v_type}] 👀 {views:,} : <a href=\"{url}\">{title}</a>")
        lines.append("")

    final_message = "\n".join(lines)

    print("\n--- Iniciando envío hacia Telegram ---")
    enviados = 0
    
    if not tg_token:
        print("⚠️ No hay TELEGRAM_BOT_TOKEN configurado en el archivo .env")
        return
        
    if tg_chat_1:
        if send_telegram_message(tg_token, tg_chat_1, final_message):
            enviados += 1
            send_telegram_document(tg_token, tg_chat_1, 'Presentacion_Top_Videos.pptx')
    else:
        print("⚠️  No hay TELEGRAM_CHAT_ID_1 en .env")
        
    if tg_chat_2:
        if send_telegram_message(tg_token, tg_chat_2, final_message):
            enviados += 1
            send_telegram_document(tg_token, tg_chat_2, 'Presentacion_Top_Videos.pptx')
    
    print(f"Envío por Telegram completo. Exitosos: {enviados}")
