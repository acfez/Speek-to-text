import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

# 🔑 KALITLARNI SHU YERGA YOZING
BOT_TOKEN = "8396537696:AAGO1_BqEr-xDGoB5cje55ZJ6GnPQDxP4LM"
REV_AI_API_KEY = "02xQa30w9gRV-yf5rEU7FrbnOwYSh1eunePYwryTK2VG8zIs6TBhYSpxWDAYtiDEsFwHXZJXjB1IvQsRTaKGd0X1V3pPE"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Rev.ai API manzillari
SUBMIT_URL = "https://api.rev.ai/speechtotext/v1/jobs"
HEADERS = {"Authorization": f"Bearer {REV_AI_API_KEY}"}

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("🎤 Ovozli xabar yuboring, men uni matnga o'giraman.")

@dp.message(F.voice)
async def handle_voice(message: Message):
    status_msg = await message.answer("📥 Ovoz yuklanmoqda...")
    file_path = f"voice_{message.message_id}.ogg"

    try:
        # 1. Telegramdan faylni yuklab olish
        file = await bot.get_file(message.voice.file_id)
        await bot.download_file(file.file_path, file_path)

        async with aiohttp.ClientSession() as session:
            # 2. Rev.ai ga faylni yuborish
            await status_msg.edit_text("📤 Serverga yuborilmoqda...")
            
            with open(file_path, 'rb') as f:
                formData = aiohttp.FormData()
                formData.add_field('media', f, filename=file_path)
                # Tilni avtomatik aniqlash yoki 'uz', 'en' deb belgilash mumkin
                formData.add_field('options', '{"metadata":"Telegram Bot", "language":"en"}') 

                async with session.post(SUBMIT_URL, headers=HEADERS, data=formData) as resp:
                    if resp.status != 200:
                        raise Exception(f"Rev.ai xatosi: {await resp.text()}")
                    job_data = await resp.json()
                    job_id = job_data["id"]

            # 3. Natijani tekshirish (Polling)
            await status_msg.edit_text("🧠 Matnga aylantirilmoqda...")
            while True:
                async with session.get(f"{SUBMIT_URL}/{job_id}", headers=HEADERS) as resp:
                    job_status = await resp.json()
                    
                    if job_status["status"] == "transcribed":
                        # Matnni yuklab olish
                        async with session.get(f"{SUBMIT_URL}/{job_id}/transcript", 
                                             headers={"Authorization": f"Bearer {REV_AI_API_KEY}", 
                                                      "Accept": "text/plain"}) as text_resp:
                            final_text = await text_resp.text()
                            await status_msg.edit_text(f"📝 **Natija:**\n\n{final_text}")
                        break
                    
                    elif job_status["status"] == "failed":
                        await status_msg.edit_text("❌ Tahlil muvaffaqiyatsiz tugadi.")
                        break
                
                await asyncio.sleep(3)

    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {str(e)}")
    
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    print("Bot ishlamoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
