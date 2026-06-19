import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import google.generativeai as genai

# === LOAD ENV ===
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY не найден в .env")

# === BOT ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === GEMINI ===
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Ты — MirazGPT, дагестанский ИИ из гор.
Отвечай только на русском, с юмором и горским стилем.
Используй: валлахи, кунак, братан, яман, машаллах.
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=SYSTEM_PROMPT
)

# === CHECK SUB ===
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# === START ===
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(
            f"Салам, кунак! 👋\nПодпишись: {CHANNEL_USERNAME}\nПотом /start"
        )
        return

    await message.answer("Валлахи братан 🔥 MirazGPT на связи!")

# === MAIN CHAT ===
@dp.message()
async def handle_message(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(f"Сначала подпишись: {CHANNEL_USERNAME}")
        return

    text = message.text

    try:
        await message.answer("Думаю, братан... 🤔")

        response = model.generate_content(text)

        if response.text:
            await message.answer(response.text)
        else:
            await message.answer("Пустой ответ, попробуй ещё раз.")

    except Exception as e:
        await message.answer("Ошибка генерации, попробуй ещё раз.")

# === RUN ===
async def main():
    print("🚀 MirazGPT запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
