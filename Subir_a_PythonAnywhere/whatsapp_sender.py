import os
import requests
from dotenv import load_dotenv

def send_whatsapp_message(phone_number, api_key, message):
    """
    Envía un mensaje de WhatsApp a través del API gratuita de CallMeBot.
    
    :param phone_number: Número de teléfono en formato internacional (Ej. +521234567890)
    :param api_key: API Key proveída por el bot al registrarse
    :param message: El texto del mensaje.
    """
    if not phone_number or not api_key:
        print(f"Faltan credenciales completas para {phone_number}.")
        return False
        
    url = "https://api.callmebot.com/whatsapp.php"
    params = {
        "phone": phone_number,
        "text": message,
        "apikey": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print(f"[OK] Mensaje enviado por WhatsApp al número {phone_number}.")
            return True
        else:
            print(f"[ERROR] No se pudo enviar el mensaje a {phone_number}. Código HTTP: {response.status_code}")
            # print(f"Detalle: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Excepción al enviar mensaje de WhatsApp: {e}")
        return False

def format_and_send_reports(top_videos_by_channel):
    """
    Formatea el diccionario del Top 5 y lo envía a los teléfonos configurados.
    """
    load_dotenv()
    
    wp_num_1 = os.getenv("WHATSAPP_NUMBER_1", "").strip()
    wp_key_1 = os.getenv("WHATSAPP_KEY_1", "").strip()
    
    wp_num_2 = os.getenv("WHATSAPP_NUMBER_2", "").strip()
    wp_key_2 = os.getenv("WHATSAPP_KEY_2", "").strip()
    
    if not top_videos_by_channel:
        print("No hay datos en el reporte para mandar por WhatsApp.")
        return

    # Armamos el texto del mensaje con Markdown básico de WhatsApp (*)
    lines = ["📊 *REPORTE TOP 5 VIDEOS POR CANAL* 📊", ""]
    
    # Para evitar romper el límite de CallmeBot mandaremos el mensaje completo si es posible.
    # Pero si son muchísimos canales es mejor ir cortando y dividiendo el mensaje.
    for channel, videos in top_videos_by_channel.items():
        lines.append(f"📺 *Canal:* {channel}")
        for index, row in videos.iterrows():
            title = row['Title']
            views = int(row['ViewCount'])
            v_type = row['VideoType']
            
            # Limitar título largo para legibilidad
            if len(title) > 65:
                title = title[:62] + "..."
            
            lines.append(f"• [{v_type}] 👀 {views:,} : {title}")
        lines.append("") # Dejar una línea en blanco como divisor

    # Unir todas las partes
    final_message = "\n".join(lines)

    print("\n--- Iniciando envío hacia WhatsApp (CallMeBot) ---")
    enviados = 0
    
    if wp_num_1 and wp_key_1:
        if send_whatsapp_message(wp_num_1, wp_key_1, final_message):
            enviados += 1
    else:
        print("⚠️  No hay credenciales en .env para WHATSAPP_NUMBER_1 y WHATSAPP_KEY_1")
        
    if wp_num_2 and wp_key_2:
        if send_whatsapp_message(wp_num_2, wp_key_2, final_message):
            enviados += 1
    else:
        print("⚠️  No hay credenciales en .env para WHATSAPP_NUMBER_2 y WHATSAPP_KEY_2")
        
    print(f"Envío por WhatsApp completo. Exitosos: {enviados}")
