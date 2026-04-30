import asyncio
import sqlite3
import feedparser
import os
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler


TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()


# RSS источники
SOURCES = {
    "финансы": [
        "https://www.vedomosti.ru/rss/business/finances",
        "https://www.kommersant.ru/rss.aspx?section=kommers_dengi"
    ],
    "технологии": [
        "https://www.vedomosti.ru/rss/technology",
        "https://www.kommersant.ru/rss.aspx?section=kommers_tech"
    ],
    "экономика": [
        "https://www.vedomosti.ru/rss/economics",
        "https://www.kommersant.ru/rss.aspx?section=kommers_economy"
    ]
}


# база данных SQLite
conn = sqlite3.connect("news.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS sent_news (
    url TEXT PRIMARY KEY
)
""")
conn.commit()


def already_sent(url: str) -> bool:
    cur.execute("SELECT 1 FROM sent_news WHERE url = ?", (url,))
    return cur.fetchone() is not None


def mark_sent(url: str):
    cur.execute("INSERT OR IGNORE INTO sent_news(url) VALUES(?)", (url,))
    conn.commit()


async def check_news():
    for category, feeds in SOURCES.items():
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)

                if not feed.entries:
                    continue

                for entry in feed.entries[:10]:
                    title = entry.get("title", "Без названия")
                    link = entry.get("link")

                    if not link:
                        continue

                    if not already_sent(link):
                        text = f"📰 Новость ({category})\n\n{title}\n{link}"
                        await bot.send_message(CHAT_ID, text)
                        mark_sent(link)

            except Exception as e:
                await bot.send_message(
                    CHAT_ID,
                    f"⚠️ Ошибка чтения RSS:\n{feed_url}\n\n{str(e)}"
                )


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_news, "interval", minutes=5)
    scheduler.start()

    await bot.send_message(CHAT_ID, "✅ Бот запущен и следит за новостями.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
