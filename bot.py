import os
import telebot
from aiohttp import web
import asyncio
import threading
from PIL import Image
import io
import json

TOKEN = "9197758020:AAEo4p1XD5v6JdNttltLYcgx42hGec7oFNg"
bot = telebot.TeleBot(TOKEN)

# Foydalanuvchi rasmlarini saqlash
user_images = {}

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Menga PDF qilmoqchi bo'lgan rasmlaringizni yuboring. Barcha rasmlarni yuborib bo'lgach /done buyrug'ini bosing yoki Mini App orqali tahrirlang.")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.from_user.id
    if user_id not in user_images:
        user_images[user_id] = []
        
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    if image.mode != 'RGB':
        image = image.convert('RGB')
        
    user_images[user_id].append(image)
    bot.reply_to(message, f"Rasm qabul qilindi! Jami: {len(user_images[user_id])} ta. /done buyrug'ini yuboring.")

@bot.message_handler(commands=['done'])
def generate_pdf(message):
    user_id = message.from_user.id
    if user_id not in user_images or not user_images[user_id]:
        bot.reply_to(message, "Siz hali rasm yubormadingiz!")
        return
        
    images = user_images[user_id]
    pdf_stream = io.BytesIO()
    images[0].save(pdf_stream, format="PDF", save_all=True, append_images=images[1:])
    pdf_stream.seek(0)
    
    bot.send_document(message.chat.id, document=pdf_stream, visible_file_name="converted_document.pdf")
    del user_images[user_id]

# --- AIOHTTP WEB SERVER & MINI APP ROUTES ---
async def handle_index(request):
    # Static papkasidagi index.html faylini ko'rsatish
    return web.FileResponse('./static/index.html')

async def run_web_server():
    app = web.Application()
    # Mini App bosh sahifasi
    app.router.add_get('/', handle_index)
    # Static fayllarni ulash (CSS, JS)
    app.router.add_static('/static/', path='./static', name='static')
    
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
    server_thread = threading.Thread(target=start_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("Bot va Mini App serveri ishga tushdi...")
    bot.infinity_polling()
