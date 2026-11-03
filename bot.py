import os
import telebot
from aiohttp import web
import asyncio
import threading
from PIL import Image
import io
import json
import base64

TOKEN = "9197758020:AAEo4p1XD5v6JdNttltLYcgx42hGec7oFNg"
bot = telebot.TeleBot(TOKEN)

user_images = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Mini App orqali rasmlarni yuklang va tahrirlang yoki botga rasmlarni ketma-ket yuboring va /done ni bosing.")

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
    bot.reply_to(message, f"Rasm qabul qilindi! Jami: {len(user_images[user_id])} ta. /done buyrug'ini bosing.")

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
    
    bot.send_document(message.chat.id, document=pdf_stream, visible_file_name="hujjat.pdf")
    del user_images[user_id]

# --- MINI APP'DAN KELGAN DATA'NI QABUL QILISH ---
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        file_name = data.get("fileName", "hujjat.pdf")
        if not file_name.endswith('.pdf'):
            file_name += '.pdf'
            
        pages = data.get("pages", [])
        if not pages:
            bot.reply_to(message, "Hech qanday rasm/sahifa tanlanmagan!")
            return

        bot.send_message(message.chat.id, "⏳ PDF tayyorlanmoqda, iltimos kuting...")

        pdf_images = []
        for page in pages:
            src = page.get("src", "")
            rotation = page.get("rotation", 0)
            
            if src.startswith("data:image"):
                # Base64 rasmni o'qish
                header, encoded = src.split(",", 1)
                img_data = base64.b64decode(encoded)
                img = Image.open(io.BytesIO(img_data))
            else:
                continue

            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Burish operatsiyasi
            if rotation != 0:
                img = img.rotate(-rotation, expand=True)

            pdf_images.append(img)

        if pdf_images:
            pdf_stream = io.BytesIO()
            pdf_images[0].save(pdf_stream, format="PDF", save_all=True, append_images=pdf_images[1:])
            pdf_stream.seek(0)

            bot.send_document(message.chat.id, document=pdf_stream, visible_file_name=file_name)
        else:
            bot.reply_to(message, "Rasmlarni qayta ishlashda xatolik yuz berdi.")

    except Exception as e:
        bot.reply_to(message, f"Xatolik yuz berdi: {str(e)}")

# --- AIOHTTP WEB SERVER ---
async def handle_index(request):
    if os.path.exists('./static/index.html'):
        return web.FileResponse('./static/index.html')
    return web.Response(text="Mini App ishlamoqda...")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle_index)
    if os.path.exists('./static'):
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
    
    print("Bot ishga tushdi...")
    bot.infinity_polling()
