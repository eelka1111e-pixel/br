import os
import telebot
from google import genai
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- НАСТРОЙКИ ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

bot = telebot.TeleBot(TOKEN)
client = genai.Client(api_key=GOOGLE_API_KEY)

# --- МИНИ-СЕРВЕР ДЛЯ RENDER (чтобы бот не умирал) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"I am alive!")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"--- Сервер проверки связи запущен на порту {port} ---")
    server.serve_forever()

# --- ЛОГИКА БОТА ---
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        print(f"Получено сообщение: {message.text}")
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=f"Ответь как дерзкий, саркастичный бро на сообщение: {message.text}"
        )
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Ошибка Gemini: {e}")
        bot.reply_to(message, "Слышь, у меня мозги заклинило. Попробуй позже.")

if __name__ == "__main__":
    # Запускаем "обманку" для Render в отдельном потоке
    threading.Thread(target=run_health_check, daemon=True).start()
    
    print("--- [СТАРТ] Бро официально вышел на связь! ---")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
