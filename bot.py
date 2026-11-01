import os
import telebot
from aiohttp import web
import asyncio
import threading

# Token to'g'ridan-to'g'ri kiritildi
TOKEN = "9197758020:AAEo4p1XD5v6JdNttltLYcgx42hGec7oFNg"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Men rasmlaringizni bitta PDF faylga birlashtirib beruvchi botman. Menga rasmlarni yuboring!")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    bot.reply_to(message, "Rasmingiz qabul qilindi! PDF yaratish jarayoni...")

# --- AIOHTTP WEB SERVER (UptimeRobot uchun) ---
async def handle(request):
    return web.Response(text="Bot is active and running!")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

def start_web_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_web_server())
    loop.run_forever()

if __name__ == '__main__':
    # Veb-serverni alohida oqimda ishga tushiramiz
    server_thread = threading.Thread(target=start_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Botni polling rejimida ishga tushiramiz
    print("Bot ishga tushdi...")
    bot.infinity_polling()
