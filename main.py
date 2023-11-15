import asyncio
from datetime import datetime, timedelta

from pyrogram import Client, filters
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/db_name"
engine = create_engine(DATABASE_URL, echo=True, future=True)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=True)
    chat_id = Column(Integer, index=True, unique=True)
    join_date = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

api_id = "YOUR_PERSON_API_ID"
api_hash = "YOUR_PERSON_API_HASH"
app = Client("my_account", api_id=api_id, api_hash=api_hash)


async def send_message(chat_id, text):
    try:
        await app.send_message(chat_id, text)
        logger.info(f"Message sent to chat_id {chat_id}: {text}")
    except Exception as e:
        logger.error(f"Error sending message to chat_id {chat_id}: {e}")


@app.on_message(filters.command("start"))
async def start(_, message):
    user = User(chat_id=message.chat.id, username=message.from_user.username)
    async with sessionmaker(engine)() as session:
        session.add(user)
        await session.commit()

    await message.reply_text("Напиши сообщение для активации бота.")

async def send_photo_function(chat_id, photo_path):
    try:
        await app.send_photo(chat_id, photo=photo_path, caption="Описание к фото")
        logger.info(f"Photo sent to chat_id {chat_id}: {photo_path}")
    except Exception as e:
        logger.error(f"Error sending photo to chat_id {chat_id}: {e}")


async def send_periodic_messages():
    photo_path = 'to_photo'
    while True:
        await asyncio.sleep(600)  # 10 минут
        await send_message(person_chat_id, "Добрый день!")

        await asyncio.sleep(5400)  # 90 минут
        await send_message(person_chat_id, "Подготовила для вас материал!")

        await send_photo_function(person_chat_id, photo_path)

        await asyncio.sleep(7200)  # 2 часа
        async with sessionmaker(engine)() as session:
            last_messages = await app.get_chat_history(person_chat_id, limit=10)
            trigger_found = any(
                message.text == "Хорошего дня!" for message in last_messages
            )

            if not trigger_found:
                await send_message(person_chat_id, "Скоро вернусь с новым материалом!")

async def count_users_today():
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    async with sessionmaker(engine)() as session:
        count = await session.query(User).filter(User.join_date >= today_start).count()
        await send_message(person_chat_id, f"Количество зарегистрированных сегодня: {count}")


@app.on_message(filters.command("users_today"))
async def users_today_command(_, message):
    await count_users_today()


if __name__ == "__main__":
    person_chat_id = "YOUR_PERSON_CHAT_ID"
    asyncio.run(asyncio.gather(app.run(), send_periodic_messages()))

