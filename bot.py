import os
import telebot
from aiohttp import web
import asyncio
import threading
from PIL import Image
import io

TOKEN = "9197758020:AAEo4p1XD5v6JdNttltLYcgx42hGec7oFNg"
bot = telebot.TeleBot(TOKEN)

# Foydalanuvchi rasmlarini vaqtincha yig'ib turish uchun lug'at
user_images = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Menga PDF qilmoqchi bo'lgan rasmlaringizni ketma-ket yuboring. Barchasini yuborib bo'lgach /done buyrug'ini bosing.")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.from_user.id
    
    # Agar foydalanuvchi uchun ro'yxat ochilmagan bo'lsa, ochamiz
    if user_id not in user_images:
        user_images[user_id] = []
        
    # Rasmning eng katta hajmini olamiz
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # Rasmni vaqtincha xotirada saqlaymiz
    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    
    # RGB formatga o'tkazamiz (PDF uchun shart)
    if image.mode != 'RGB':
        image = image.convert('RGB')
        
    user_images[user_id].append(image)
    bot.reply_to(message, f"Rasm qabul qilindi! Jami rasmlar: {len(user_images[user_id])}. Yana yuboring yoki /done ni bosing.")

@bot.message_handler(commands=['done'])
def generate_pdf(message):
    user_id = message.from_user.id
    
    if user_id not in user_images or not user_images[user_id]:
        bot.reply_to(message, "Siz hali birorta rasm yubormadingiz!")
        return
        
    bot.reply_to(message, "PDF fayl tayyorlanmoqda, biroz kuting...")
    
    images = user_images[user_id]
    pdf_stream = io.BytesIO()
    
    # Birinchi rasmni olib, qolganlarini unga qo'shamiz va PDF qilamiz
    images[0].save(
        pdf_stream,
        format="PDF",
        save_all=True,
        append_images=images[1:]
    )
    pdf_stream.seek(0)
    
    # Faylni foydalanuvchiga yuboramiz
    bot.send_document(message.chat.id, document=pdf_stream, visible_file_name="converted_document.pdf")
    
    # Xotirani tozalaymiz
    del user_images[user_id]

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
    server_thread = threading.Thread(target=start_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("Bot ishga tushdi...")
    bot.infinity_polling()
