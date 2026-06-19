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

# === ПАМЯТЬ ===
user_names = {}
user_history = {}

# === СТИЛЬ (СПОКОЙНЫЙ) ===
SYSTEM_PROMPT = """
Ты — полезный Telegram ассистент.

Правила:
- не используй звёздочки *
- не делай форматирование
- пиши просто и чисто
- отвечай по делу

Иногда:
- "Салам алейкум" при приветствии
- "ваалейкум ассалам" в ответ
- иногда слово "брат"
- иногда "машаллах" если уместно
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# === ПРОВЕРКА ПОДПИСКИ ===
async def is_subscribed(user_id: int) -> bool:
    try:
        m = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status in ["member", "administrator", "creator"]
    except:
        return False


# === КАРТИНКИ (NanoBanana / Pollinations) ===
def generate_image(prompt: str):
    return f"https://image.pollinations.ai/prompt/{prompt}"


# === START ===
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    user_names[user_id] = message.from_user.first_name

    if not await is_subscribed(user_id):
        await message.answer(f"Подпишись на канал: {CHANNEL_USERNAME}")
        return

    await message.answer("Салам алейкум. Я на связи.")


# === ОСНОВНОЙ ХЕНДЛЕР ===
@dp.message()
async def chat(message: types.Message):
    user_id = message.from_user.id
    name = user_names.get(user_id, "брат")

    if not await is_subscribed(user_id):
        await message.answer("Сначала подпишись на канал.")
        return

    text = message.text

    # === САЛАМ ===
    if "салам" in text.lower():
        await message.answer("ваалейкум ассалам")
        return

    # === КАРТИНКИ ===
    if any(x in text.lower() for x in ["нарисуй", "картинку", "image", "генерируй"]):
        img = generate_image(text)
        await message.answer_photo(img)
        return

    # === ИСТОРИЯ (простая память) ===
    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append(text)
    user_history[user_id] = user_history[user_id][-5:]  # последние 5 сообщений

    context = "\n".join(user_history[user_id])

    try:
        resp = model.generate_content(context)
        await message.answer(resp.text)
    except:
        await message.answer("ошибка, попробуй ещё раз")


# === RUN ===
async def main():
    print("bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
