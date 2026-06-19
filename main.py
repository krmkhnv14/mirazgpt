import asyncio
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
Ты MirazGPT — умный кавказский ИИ ассистент.
Отвечай по-русски, просто, без религиозных вставок, без лишних символов и звездочек.
Помогай с обучением, программированием и объяснениями.
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
        return True  # не ломаем бота из-за проверки

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Бот запущен. Напиши вопрос.")

@dp.message()
async def chat(message: types.Message):
    try:
        response = model.generate_content(message.text)

        text = getattr(response, "text", None)
        if not text:
            await message.answer("Не удалось получить ответ. Попробуй еще раз.")
            return

        await message.answer(text)

    except Exception as e:
        print("Gemini error:", e)
        await message.answer("Ошибка генерации. Попробуй позже.")

async def main():
    print("bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
