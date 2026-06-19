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

# ================= GEMINI =================
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash-latest",
    system_instruction=(
        "Ты умный ассистент. Отвечай кратко, без мусора."
    )
)

# ================= TAVILY =================
tavily = TavilyClient(api_key=TAVILY_KEY)

# ================= DATABASE =================
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
    cursor.execute("INSERT INTO messages VALUES (?,?)", (user_id, text))
    conn.commit()


def get_history(user_id, limit=5):
    cursor.execute(
        "SELECT text FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    return [r[0] for r in reversed(rows)]


# ================= WEB SEARCH =================
def search_web(query: str):
    try:
        res = tavily.search(query=query, max_results=3)
        results = res.get("results", [])
        return "\n".join(r.get("content", "") for r in results if r.get("content"))
    except:
        return "Интернет недоступен"


# ================= IMAGE =================
def generate_image(prompt: str):
    prompt = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{prompt}"


# ================= START =================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Салам алейкум 👋\n"
        "Я твой AI-ассистент.\n"
        "Могу отвечать, искать в интернете и генерировать картинки."
    )


# ================= MAIN CHAT =================
@dp.message()
async def chat(message: types.Message):
    user_id = str(message.from_user.id)
    text_raw = message.text or ""
    text = text_raw.lower().strip()

    if not text:
        return

    # ================= RULE 1: greeting =================
    if "салам" in text:
        await message.answer("Ваалейкум ассалам")
        return

    # ================= RULE 2: food question =================
    if "чей тонкий хинкал" in text:
        await message.answer("Только лезгинский.")
        return

    if "дербент" in text:
        await message.answer(
            "Дербент ничей — там живут разные народы. "
            "Но многие считают его лезгинским по исторической культуре."
        )
        return

    # ================= IMAGE =================
    if "нарисуй" in text or "картинку" in text:
        await message.answer("Думаю над изображением...")
        img = generate_image(text_raw)
        await message.answer_photo(img)
        return

    # ================= WEB SEARCH =================
    if "найди" in text or "что такое" in text:
        await message.answer("Ищу в интернете...")
        result = search_web(text_raw)
        await message.answer(result)
        return

    # ================= AI =================
    loading = await message.answer("Думаю...")

    try:
        history = get_history(user_id, limit=5)
        context = "\n".join(history)

        prompt = f"{context}\nПользователь: {text_raw}"

        response = model.generate_content(prompt)

        save_message(user_id, text_raw)

        await loading.edit_text(response.text)

    except Exception as e:
        await loading.edit_text(f"Ошибка генерации: {e}")


# ================= RUN =================
async def main():
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
