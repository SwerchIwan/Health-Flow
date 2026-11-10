import asyncio
import html as html_lib
import logging
import sys
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)


TOKEN = getenv("TELEGRAM_BOT_TOKEN", "")
SITE_URL = getenv("SITE_URL", "http://127.0.0.1:8000")
SUPPORT_USERNAME = getenv("SUPPORT_USERNAME", "")

dp = Dispatcher()
router = Router()

DIVIDER = "━━━━━━━━━━━━━━━━━━━━"


class QuestionStates(StatesGroup):
    waiting = State()


# ---------- Клавиатуры ----------

def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Частые вопросы"), KeyboardButton(text="🩺 Стать специалистом")],
            [KeyboardButton(text="🌐 Открыть сайт"), KeyboardButton(text="💬 Написать поддержке")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите пункт меню",
    )


def faq_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🩺 Как стать специалистом?", callback_data="faq:specialist")],
        [InlineKeyboardButton(text="📄 Какие документы нужны?", callback_data="faq:docs")],
        [InlineKeyboardButton(text="🤖 Как работает нейросеть?", callback_data="faq:ai")],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="menu")],
    ])


def back_to_faq() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К вопросам", callback_data="faq")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")],
    ])


def site_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Открыть Health Flow AI", url=SITE_URL)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")],
    ])


def welcome_text(name: str) -> str:
    return (
        f"👋 <b>Привет, {name}!</b>\n"
        f"Я — бот поддержки <b>Health Flow AI</b>.\n\n"
        f"Помогу разобраться с профилем, подписками и работой ИИ-помощника.\n"
        f"{DIVIDER}\n"
        f"💡 Выберите раздел кнопками ниже или просто напишите вопрос — "
        f"мы передадим его в поддержку."
    )


FAQ = {
    "specialist": (
        "🩺 <b>Как стать специалистом?</b>\n\n"
        "1. Зарегистрируйтесь и войдите в аккаунт на сайте.\n"
        "2. В профиле нажмите «Стать специалистом».\n"
        "3. Прикрепите информацию об образовании и документы.\n"
        "4. В течение <b>7 дней</b> заявку проверит отдел кадров и свяжется с вами."
    ),
    "docs": (
        "📄 <b>Какие документы нужны?</b>\n\n"
        "• документ, подтверждающий личность;\n"
        "• документы об образовании;\n"
        "• аттестат.\n\n"
        "Все документы обязательно прикладываются к заявке."
    ),
    "ai": (
        "🤖 <b>Как работает нейросеть?</b>\n\n"
        "Health Flow AI — модель, специально обученная на медицинских данных. "
        "Она работает прямо на сайте: опишите симптом или вопрос — "
        "и получите быстрый ответ с рекомендациями.\n\n"
        "⚠️ Ответы ИИ носят справочный характер и не заменяют консультацию врача."
    ),
}


# ---------- Обработчики ----------

@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    name = html_lib.escape(message.from_user.full_name)
    await message.answer(
        f"<b>Health Flow AI</b>\n<i>The pulse of modern medicine</i>\n\n" + welcome_text(name),
        reply_markup=main_menu(),
    )


@router.message(Command("menu"))
@router.message(F.text == "🏠 Главное меню")
async def command_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🏠 <b>Главное меню</b>\nВыберите, чем я могу помочь:",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def command_help(message: Message) -> None:
    await message.answer(
        "🧭 <b>Команды</b>\n\n"
        "/start — начать заново\n"
        "/menu — главное меню\n"
        "/faq — частые вопросы\n"
        "/site — открыть сайт\n"
        "/help — эта справка",
        reply_markup=main_menu(),
    )


@router.message(Command("faq"))
@router.message(F.text == "❓ Частые вопросы")
async def show_faq(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"❓ <b>Частые вопросы</b>\n{DIVIDER}\nВыберите тему:",
        reply_markup=faq_menu(),
    )


@router.callback_query(F.data == "faq")
async def cb_faq(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text(
        f"❓ <b>Частые вопросы</b>\n{DIVIDER}\nВыберите тему:",
        reply_markup=faq_menu(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("faq:"))
async def cb_faq_answer(call: CallbackQuery) -> None:
    key = call.data.split(":", 1)[1]
    text = FAQ.get(key)
    if not text:
        await call.answer("Вопрос не найден", show_alert=True)
        return
    await call.message.edit_text(text + f"\n{DIVIDER}", reply_markup=back_to_faq())
    await call.answer()


@router.message(Command("site"))
@router.message(F.text == "🌐 Открыть сайт")
async def show_site(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🌐 <b>Health Flow AI</b>\nЛичный дневник, ИИ-помощник и связь со специалистами в одном месте.",
        reply_markup=site_menu(),
    )


@router.message(F.text == "🩺 Стать специалистом")
async def ask_specialist(message: Message) -> None:
    await message.answer(FAQ["specialist"] + f"\n{DIVIDER}", reply_markup=back_to_faq())


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    name = html_lib.escape(call.from_user.full_name)
    await call.message.edit_text(
        f"🏠 <b>Главное меню</b>\n\n" + welcome_text(name),
        reply_markup=faq_menu(),
    )
    await call.answer()


@router.message(F.text == "💬 Написать поддержке")
async def ask_support(message: Message, state: FSMContext) -> None:
    await state.set_state(QuestionStates.waiting)
    await message.answer(
        "💬 <b>Напишите ваш вопрос</b>\n"
        "Опишите ситуацию одним сообщением — оператор ответит здесь же.\n\n"
        "<i>Чтобы отменить — отправьте /menu</i>",
    )


@router.message(QuestionStates.waiting)
async def receive_question(message: Message, state: FSMContext) -> None:
    await state.clear()
    text = (message.text or "").strip()
    preview = html_lib.escape(text[:300] + ("…" if len(text) > 300 else ""))
    await message.answer(
        f"✅ <b>Вопрос принят!</b>\n{DIVIDER}\n"
        f"<blockquote>{preview}</blockquote>\n"
        f"🕒 Поддержка свяжется с вами в ближайшее время.",
        reply_markup=main_menu(),
    )
    if SUPPORT_USERNAME:
        await message.bot.send_message(
            f"@{SUPPORT_USERNAME.lstrip('@')}",
            f"📩 Вопрос от {html_lib.escape(message.from_user.full_name)} "
            f"(id {message.from_user.id}):\n\n{preview}",
        )


@router.message()
async def answer(message: Message) -> None:
    await message.answer(
        "Мы получили ваш вопрос и передали его поддержке! 🕒\n\n"
        "Пока ждёте — загляните в <b>частые вопросы</b> 🙋",
        reply_markup=main_menu(),
    )


async def main() -> None:
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
