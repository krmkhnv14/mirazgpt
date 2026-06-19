import asyncio
import os
import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import google.generativeai as genai
from tavily import TavilyClient

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

genai.configure(api_key=GEMINI_API_KEY)

tavily = TavilyClient(api_key=TAVILY_KEY)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "Ты умный ассистент. Отвечай кратко, без звёздочек и мусора. "
        "Иногда используй 'брат' или 'кунак' но не спамь этим."
    )
)

# ================= DATABASE =================
conn = sqlite3.connect("memory.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id TEXT,
    text TEXT
)
""")
conn.commit()


def save_message(user_id, text):
    cursor.execute("INSERT INTO messages VALUES (?,?)", (user_id, text))
    conn.commit()


def get_history(user_id, limit=10):
    cursor.execute(
        "SELECT text FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    return [r[0] for r in reversed(rows)]


# ================= INTERNET =================
def search_web(query: str):
    try:
        res = tavily.search(query=query, max_results=3)
        return "\n".join([r["content"] for r in res["results"]])
    except:
        return "Интернет недоступен"


# ================= IMAGE =================
def generate_image(prompt: str):
    prompt = prompt.replace(" ", "%20")
    return f"https://image.pollinations.ai/prompt/{prompt}"


# ================= CHECK =================
async def is_subscribed(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return True


# ================= START =================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Салам алейкум")


# ================= MAIN CHAT =================
@dp.message()
async def chat(message: types.Message):
    user_id = str(message.from_user.id)
    text = message.text or ""

    if "салам" in text.lower():
        await message.answer("Ваалейкум ассалам")
        return

    # IMAGE
    if any(x in text.lower() for x in ["нарисуй", "картинку"]):
        await message.answer("Думаю над изображением...")
        img = generate_image(text)
        await message.answer_photo(img)
        return

    # INTERNET SEARCH
    if "найди" in text.lower() or "что такое" in text.lower():
        await message.answer("Ищу в интернете...")
        result = search_web(text)
        await message.answer(result)
        return

    # LOADING UX
    loading = await message.answer("Думаю...")

    try:
        history = get_history(user_id)
        context = "\n".join(history)

        full_prompt = f"{context}\nПользователь: {text}"

        response = model.generate_content(full_prompt)

        save_message(user_id, text)

        await loading.edit_text(response.text)

    except:
        await loading.edit_text("Ошибка генерации")


async def main():
    print("MirazGPT 2.0 started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
