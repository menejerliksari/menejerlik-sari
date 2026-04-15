import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    telegram_id = str(user.id)
    full_name = user.full_name

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Menejerlik sari kabinetini ochish",
                    web_app=WebAppInfo(
                        url=f"{WEBAPP_URL}/?telegram_id={telegram_id}"
                    )
                )
            ]
        ],
        resize_keyboard=True
    )

    admin_text = ""
    if telegram_id == ADMIN_ID:
        admin_text = "\nSiz adminsiz."

    await message.answer(
        f"Salom, {full_name}!\n"
        f"Menejerlik sari tizimiga xush kelibsiz.\n"
        f"ID: {telegram_id}"
        f"{admin_text}",
        reply_markup=keyboard,
    )


async def main():
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())