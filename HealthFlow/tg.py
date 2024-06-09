"""
import asyncio
import logging
import sys
from os import getenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message


TOKEN = "7051832167:AAEblaND5f_n3-mX9fkjzdS5jDiTt_3Xwd8"
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Привет, это бот поддержки HealthFlow задавайте ваш вопрос, {html.bold(message.from_user.full_name)}!")


@dp.message()
async def supp_message(message: Message) -> None:
        await message.answer(f"Мы скоро ответим вам на ваш вопрос. Ожидайте!")


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

"""

from celery import shared_task
from pyrogram import Client
from asgiref.sync import async_to_sync
from pyrogram.raw import functions

api_id = 28876843
api_hash = "6db5ddea74af86bfd8d5bf90d08960e8"

@shared_task
def send_code_to_user_task(phone, code):
    async def get_user_id_by_phone(phone):
        async with Client("account", api_id, api_hash) as app:
            result = await app.send(
                functions.contacts.ImportContacts(
                    contacts=[{"phone": phone}]
                )
            )
            user_id = result.users[0].id if result.users else None
            print(user_id)
            return user_id

    async def send_code(phone, code):
        print(phone)
        async with Client("account", api_id, api_hash) as app:
            user_id = await get_user_id_by_phone(phone)
            if user_id:
                await app.send_message(user_id, code)
            else:
                raise ValueError("User not found")

    # Используйте async_to_sync для запуска асинхронной функции в синхронном контексте Celery
    async_to_sync(send_code)(phone, code)

