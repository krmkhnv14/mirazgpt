import asyncio
import os
import aiohttp
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

users = {}

SYSTEM_PROMPT = """
Ты — MirazGPT, полезный Telegram ассистент.
Отвечай кратко и понятно.
Иногда можешь писать "Салам алейкум", "брат", "машаллах", но редко.
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=SYSTEM_PROMPT
)

# === ПРОВЕРКА ПОДПИСКИ ===
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# === ГЕНЕРАЦИЯ КАРТИНОК ===
async def generate_image(prompt: str):
    url = f"https://image.pollinations.ai/prompt/{prompt}"
    return url


@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    users[user_id] = message.from_user.first_name

    if not await is_subscribed(user_id):
        await message.answer(f"Подпишись на канал: {CHANNEL_USERNAME}")
        return

    await message.answer("MirazGPT онлайн 🤖")


@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    name = users.get(user_id, "брат")

    if not await is_subscribed(user_id):
        await message.answer("Сначала подпишись на канал")
        return

    text = message.text.lower()

    # === ЕСЛИ ХОТЯТ КАРТИНКУ ===
    if any(x in text for x in ["нарисуй", "картинку", "generate", "image"]):
        prompt = message.text

        await message.answer("Рисую, брат... 🎨")

        img_url = await generate_image(prompt)

        await message.answer_photo(photo=img_url)
        return

    # === ОБЫЧНЫЙ ЧАТ ===
    try:
        response = model.generate_content(message.text)
        await message.answer(response.text)
    except:
        await message.answer("Ошибка, попробуй ещё раз")


async def main():
    print("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
