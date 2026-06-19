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
Ты MirazGPT — дагестанский ИИ. Отвечай по-русски, с юмором.
Не используй звёздочки, markdown-разметку и лишние символы.
Не упоминай религию.
Отвечай естественно, без перегибов.
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

    await message.answer(
        "Салам алейкум. Бот запущен.\n"
        "Пиши вопросы — отвечу нормально и по делу."
    )


@dp.message()
async def chat(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer("Сначала подпишись")
        return

    try:
        res = model.generate_content(message.text or "")

        text = res.text.strip() if res.text else ""

        if not text:
            await message.answer("Не получилось ответить, попробуй ещё раз")
            return

        await message.answer(text)

    except Exception:
        await message.answer("Не получилось ответить, попробуй ещё раз")


async def main():
    print("bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
