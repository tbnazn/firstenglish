import os
import csv
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import openai

load_dotenv()
API_TOKEN = os.getenv("TG_API_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
openai.api_key = OPENAI_KEY

# Загрузка слов
with open("wordlist.csv", encoding='utf-8') as f:
    words = list(csv.reader(f))[1:]  # Пропускаем заголовок

users = set()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    users.add(message.chat.id)
    await message.answer("Вы подписаны на ежедневные слова!")

def get_word_by_index(idx):
    if idx < len(words):
        return words[idx][0], words[idx][1]
    return None, None

async def send_word(word, translation, user_id):
    # Здесь — генерация блока через OpenAI
    prompt = f"""
Английское слово: {word}
Перевод: {translation}
Придумай для изучающего английский словесный блок по следующим пунктам:
1. Ассоциации и мнемоники, чтобы легко запомнить (по-русски и по-английски, если есть шутки или пошлость — добавь);
2. Кратко этимология и значение;
3. 2-3 коротких примера в предложениях или цитатах (с переводом);
4. Синтаксис и морфология;
5. Синонимы/антонимы;
6. Фразовые глаголы;
7. 2-3 слова, похожих по написанию/звучанию (с переводом).
Ответ четко по пунктам, без лишнего текста.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.2
    )
    await bot.send_message(user_id, response.choices[0].message.content)

def schedule_jobs():
    hours = [9, 12, 15, 18, 21]
    for idx, hour in enumerate(hours):
        scheduler.add_job(lambda idx=idx: send_words_all(idx), "cron", hour=hour, minute=0, id=f"job_{hour}")

async def send_words_all(idx):
    word_idx = idx  # Просто пример, в проде — учитывать день и пользователя!
    word, translation = get_word_by_index(word_idx)
    if not word:
        return
    for user_id in users:
        await send_word(word, translation, user_id)

if __name__ == '__main__':
    schedule_jobs()
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)
