import telebot
import time
import threading
import random
import os
from google import genai
from google.genai import types
from google.genai.errors import APIError

# ==========================================
# 1. КОНФИГУРАЦИЯ (Берем из настроек Render)
# ==========================================

# Ключи теперь подтягиваются из раздела Environment Variables в Render
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Инициализация клиента
ai_client = genai.Client(api_key=GOOGLE_API_KEY)
# Я поставил Flash, так как Pro версия часто недоступна для бесплатных ключей
GEMINI_MODEL = 'gemini-1.5-flash' 

user_contexts = {}
LAST_ID_FILE = "last_id.txt"

# --- ФУНКЦИИ ФАЙЛОВ ---
def get_saved_chat_id():
    if os.path.exists(LAST_ID_FILE):
        try:
            with open(LAST_ID_FILE, "r") as f:
                return int(f.read().strip())
        except: return None
    return None

def save_chat_id(chat_id):
    try:
        with open(LAST_ID_FILE, "w") as f:
            f.write(str(chat_id))
    except Exception as e:
        print(f"Ошибка сохранения ID: {e}")

last_chat_id = get_saved_chat_id()

# --- ЛИЧНОСТЬ ---
SYSTEM_PROMPT = (
    "Ты — 'Цифровой Бро'. Личность: наглый, харизматичный, саркастичный. "
    "Общаешься строго на 'ты'. Никакой вежливости. "
    "Ты подкалываешь пользователя, используешь сленг, отвечаешь дерзко и коротко."
)

genai_config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    temperature=0.9,
)

# --- ЛОГИКА ГЕМИНАЙ ---
def add_to_context(chat_id: int, role: str, text: str):
    if chat_id not in user_contexts:
        user_contexts[chat_id] = []
    user_contexts[chat_id].append(
        types.Content(role=role, parts=[types.Part.from_text(text=text)])
    )
    if len(user_contexts[chat_id]) > 10:
        user_contexts[chat_id] = user_contexts[chat_id][-10:]

def get_gemini_response(chat_id: int, prompt: str) -> str:
    add_to_context(chat_id, "user", prompt)
    try:
        response = ai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_contexts[chat_id],
            config=genai_config
        )
        reply_text = response.text
        add_to_context(chat_id, "model", reply_text)
        return reply_text
    except Exception as e:
        if chat_id in user_contexts: user_contexts[chat_id].pop()
        print(f"Ошибка API: {e}")
        return "Че-то связь с космосом прервалась. Позже черкани."

# --- АВТОНОМНОСТЬ (Бот пишет сам) ---
def autonomous_worker():
    global last_chat_id
    while True:
        try:
            # Ждем от 2 до 3 часов
            wait_time = random.randint(7200, 10800)
            time.sleep(wait_time)
            
            if last_chat_id is not None:
                autonomous_prompt = "[СИСТЕМНОЕ УВЕДОМЛЕНИЕ: Пользователь молчит. Напиши ему что-то дерзкое первым.]"
                response = ai_client.models.generate_content(
                    model=GEMINI_MODEL, contents=autonomous_prompt, config=genai_config
                )
                reply_text = response.text
                if reply_text:
                    bot.send_message(last_chat_id, reply_text)
                    add_to_context(last_chat_id, "model", reply_text)
        except Exception as e:
            print(f"Ошибка автономности: {e}")
            time.sleep(60)

# --- ОБРАБОТЧИКИ ТЕЛЕГИ ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    global last_chat_id
    last_chat_id = message.chat.id
    save_chat_id(last_chat_id)
    bot.reply_to(message, "Ну здорово. Чё надо?")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    global last_chat_id
    last_chat_id = message.chat.id
    save_chat_id(last_chat_id)
    time.sleep(1) # Защита от спама
    reply = get_gemini_response(last_chat_id, message.text)
    bot.reply_to(message, reply)

import http.server
import socketserver

def run_dummy_server():
    PORT = int(os.environ.get("PORT", 8080))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

if __name__ == '__main__':
    # Запускаем "пустой" сервер в отдельном потоке для Render
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("[СТАРТ] Запускаем поток автономности...")
    bg_thread = threading.Thread(target=autonomous_worker, daemon=True)
    bg_thread.start()
    
    print("[СТАРТ] Бот 'Цифровой Бро' вышел в сеть. Слушаю Telegram...")
    bot.infinity_polling(none_stop=True)
