import asyncio
import logging
import sys
from os import getenv
from aiogram import Bot, Dispatcher, html, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


TOKEN = "7051832167:AAEblaND5f_n3-mX9fkjzdS5jDiTt_3Xwd8"
dp = Dispatcher()

questions_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Часто задаваемые вопросы 👀👀👀')]
], resize_keyboard=True, input_field_placeholder="Выберите пункт меню.")

questions = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Как стать специалистом?')],
    [KeyboardButton(text='Какие документы требуется чтобы стать специалистом?')],
    [KeyboardButton(text='Как работает нейросеть?')],
    [KeyboardButton(text='< Назад в меню')],
], resize_keyboard=True, input_field_placeholder="Выберите пункт меню.")


inline_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='HealthFlow AI', url='https://www.google.co.uk/')]
])

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.reply(f"Привет, это бот поддержки HealthFlow напишите команду /menu для продолжения, {html.bold(message.from_user.full_name)}? Наш сайт:", reply_markup=inline_menu)


@router.message(Command('menu'))
async def command_menu_handler(message: Message) -> None:
    await message.answer(text="Доступные команды:", reply_markup=questions_menu)


@router.message(lambda message: message.text == 'Часто задаваемые вопросы 👀👀👀')
async def show_questions(message: Message):
    await message.answer(text="Выберите вопрос:", reply_markup=questions)


@router.message(lambda message: message.text == 'Как стать специалистом?')
async def answer_question_1(message: Message):
    await message.answer(text="На нашем сайте предусмотрена процедура становлением специалистом. Для этого вам требуется пройти регистрацию, после чего войти в ваш аккаунт. Где после нажаития на кнопку Стать специалистом, вы сможете прикрепить информацию о вашем образовании. В течении 7 дней ваше резюме будет проверено и наш отдел кадров с вами свяжется.")


@router.message(lambda message: message.text == 'Какие документы требуется чтобы стать специалистом?')
async def answer_question_2(message: Message):
    await message.answer(text="В перечень документов для становления специалиста входят: документы подтверждающие личность, документы о получении образования, аттестат. Данные документы обязательно должны быть приложены в запросе на становления специалистом.")


@router.message(lambda message: message.text == 'Как работает нейросеть?')
async def answer_question_3(message: Message):
    await message.answer(text="HealthFlow AI - специально обученная модель, которая располагается на одноименном сайте. Данная модель поможет быстрее найти ответ на ваш интересующий вопрос.")


@router.message(lambda message: message.text == '< Назад в меню')
async def back_to_menu(message: Message):
    await command_menu_handler(message)


@router.message()
async def answer(message: Message):
    await message.answer(text="Мы получили ваш вопрос, ожидайте ответа от нашей поддержки!")



async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())




