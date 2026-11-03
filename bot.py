import os
import telebot
from aiohttp import web
import asyncio
import threading
from PIL import Image
import io
import base64

TOKEN = "9197758020:AAEo4p1XD5v6JdNttltLYcgx42hGec7oFNg"
bot = telebot.TeleBot(TOKEN)

async def handle_index(request):
    if os.path.exists('./static/index.html'):
        return web.FileResponse('./static/index.html')
    return web.Response(text="Mini App ishlamoqda...")

# --- MINI APP DAN KELGAN POST SO'ROVNI QABUL QILISH ---
async def handle_api_pdf(request):
    try:
        data = await request.json()
        user_id = data.get("userId")
        file_name = data.get("fileName", "hujjat.pdf")
        if not file_name.endswith('.pdf'):
            file_name += '.pdf'
            
        pages = data.get("pages", [])
        if not user_id or not pages:
            return web.json_response({"success": False, "error": "Ma'lumotlar topilmadi"})

        pdf_images = []
        for page in pages:
            src = page.get("src", "")
            rotation = page.get("rotation", 0)
            
            if src.startswith("data:image"):
                header, encoded = src.split(",", 1)
                img_data = base64.b64decode(encoded)
                img = Image.open(io.BytesIO(img_data)).convert('RGB')
            else:
                continue

            if rotation != 0:
                img = img.rotate(-rotation, expand=True)

            pdf_images.append(img)

        if pdf_images:
            pdf_stream = io.BytesIO()
            pdf_images[0].save(pdf_stream, format="PDF", save_all=True, append_images=pdf_images[1:])
            pdf_stream.seek(0)

            # PDF ni to'g'ridan-to'g'ri foydalanuvchiga yuboramiz
            bot.send_document(user_id, document=pdf_stream, visible_file_name=file_name)
            return web.json_response({"success": True})
        else:
            return web.json_response({"success": False, "error": "Rasmlar topilmadi"})

    except Exception as e:
        return web.json_response({"success": False, "error": str(e)})

async def run_web_server():
    # Katta hajmli rasmlar o'tishi uchun client_max_size ni kattalashtiramiz (50MB)
    app = web.Application(client_max_size=50*1024*1024)
    app.router.add_get('/', handle_index)
    app.router.add_post('/create-pdf', handle_api_pdf)
    
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

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Bot tayyor. Mini App orqali rasmlarni yuklab PDF qiling.")

if __name__ == '__main__':
    server_thread = threading.Thread(target=start_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("Bot ishga tushdi...")
    bot.infinity_polling()
