import telebot
import time
import threading
import random
import os
import http.server
import socketserver
from google import genai
from google.genai import types

# --- КОНФИГУРАЦИЯ ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
ai_client = genai.Client(api_key=GOOGLE_API_KEY)
GEMINI_MODEL = 'gemini-1.5-flash'

# --- ПЕРЕМЕННЫЕ ---
user_contexts = {}
SYSTEM_PROMPT = "Ты — 'Цифровой Бро'. Ты наглый, харизматичный, саркастичный. Общаешься строго на 'ты', используешь сленг и подколы."
genai_config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.9)

# --- ЛОГИКА ---
def get_gemini_response(chat_id, prompt):
    if chat_id not in user_contexts: user_contexts[chat_id] = []
    user_contexts[chat_id].append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))
    try:
        response = ai_client.models.generate_content(model=GEMINI_MODEL, contents=user_contexts[chat_id], config=genai_config)
        user_contexts[chat_id].append(types.Content(role="model", parts=[types.Part.from_text(text=response.text)]))
        return response.text
    except:
        return "Че-то связь с космосом прервалась. Позже черкани."

@bot.message_handler(commands=['start'])
def start(m): bot.reply_to(m, "Ну здорово. Чё надо?")

@bot.message_handler(func=lambda m: True)
def chat(m):
    res = get_gemini_response(m.chat.id, m.text)
    bot.reply_to(m, res)

# --- СЕРВЕР ДЛЯ RENDER ---
def run_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    print("Бро в сети!")
    bot.infinity_polling(none_stop=True)
