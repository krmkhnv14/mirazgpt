\import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Ты MirazGPT — дагестанский ИИ. Отвечай по-русски, с юмором.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT
)

async def is_subscribed(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

@dp.message(Command("start"))
async def start(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer("Подпишись на канал сначала")
        return
    await message.answer("Бот работает 🔥 пиши")

@dp.message()
async def chat(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer("Сначала подпишись")
        return

    try:
        res = model.generate_content(message.text)
        await message.answer(res.text)
    except:
        await message.answer("Ошибка")

async def main():
    print("bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
