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
Ты MirazGPT — умный кавказский ИИ помощник.
Отвечай по-русски, просто и понятно.
Без звёздочек, markdown и лишних символов.
Без религиозных упоминаний.
Давай полезные ответы, объяснения и туториалы.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT
)


# ================= CHECK SUB =================
async def is_subscribed(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# ================= CLEAN TEXT =================
def clean(text: str) -> str:
    if not text:
        return ""

    text = text.replace("*", "")
    text = text.replace("_", "")
    text = text.replace("`", "")
    text = text.strip()

    return text


# ================= SAFE GEMINI CALL =================
def ask_gemini(prompt: str):
    for _ in range(2):  # retry 2 раза
        try:
            res = model.generate_content(prompt)

            if res and res.text:
                text = clean(res.text)
                if len(text) > 0:
                    return text
        except:
            continue

    return "Не удалось получить ответ. Попробуй ещё раз."


# ================= START =================
@dp.message(Command("start"))
async def start(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer("Подпишись на канал сначала")
        return

    await message.answer(
        "Салам. Я MirazGPT.\n"
        "Могу объяснять, помогать с задачами и делать туториалы.\n"
        "Пиши что нужно."
    )


# ================= CHAT =================
@dp.message()
async def chat(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer("Сначала подпишись")
        return

    text = message.text or ""

    if not text.strip():
        await message.answer("Напиши текст нормально")
        return

    answer = ask_gemini(text)
    await message.answer(answer)


async def main():
    print("MirazGPT started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
