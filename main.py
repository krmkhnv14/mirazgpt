import asyncio
import os
import sqlite3
import urllib.parse

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import google.generativeai as genai
from tavily import TavilyClient

# ================= ENV =================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

# ================= BOT =================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= AI =================
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "Ты умный ассистент. Отвечай кратко и по делу. "
        "Без мусора и лишних символов."
    )
)

# ================= TAVILY =================
tavily = TavilyClient(api_key=TAVILY_KEY)

# ================= DATABASE (FIXED) =================
conn = sqlite3.connect("memory.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id TEXT,
    text TEXT
)
""")
conn.commit()


def save_message(user_id, text):
    try:
        cursor.execute("INSERT INTO messages VALUES (?,?)", (user_id, text))
        conn.commit()
    except Exception as e:
        print("DB error:", e)


def get_history(user_id, limit=5):
    cursor.execute(
        "SELECT text FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    return [r[0] for r in reversed(rows)]


# ================= INTERNET (FIXED) =================
def search_web(query: str):
    try:
        res = tavily.search(query=query, max_results=3)
        results = res.get("results", [])
        return "\n".join(r.get("content", "") for r in results if r.get("content"))
    except Exception as e:
        return f"Ошибка поиска: {e}"


# ================= IMAGE (FIXED URL) =================
def generate_image(prompt: str):
    prompt = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{prompt}"


# ================= CHECK SUB =================
async def is_subscribed(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return True


# ================= START =================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Салам")


# ================= MAIN CHAT =================
@dp.message()
async def chat(message: types.Message):
    user_id = str(message.from_user.id)
    text = (message.text or "").strip().lower()

    if not text:
        return

    # greeting
    if "салам" in text:
        await message.answer("Ваалейкум ассалам")
        return

    # image generation
    if "нарисуй" in text or "картинку" in text:
        await message.answer("Думаю над изображением...")
        img = generate_image(message.text)
        await message.answer_photo(img)
        return

    # web search
    if "найди" in text or "что такое" in text:
        await message.answer("Ищу в интернете...")
        result = search_web(message.text)
        await message.answer(result)
        return

    # typing indicator
    loading = await message.answer("Думаю...")

    try:
        history = get_history(user_id, limit=5)
        context = "\n".join(history)

        full_prompt = f"{context}\nПользователь: {message.text}"

        response = model.generate_content(full_prompt)

        save_message(user_id, message.text)

        await loading.edit_text(response.text)

    except Exception as e:
        await loading.edit_text(f"Ошибка генерации: {e}")


# ================= RUN =================
async def main():
    print("MirazGPT started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
