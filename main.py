import asyncio
import logging
import os
from html import escape

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "").strip().rstrip("/")
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "gimmemo_webhook_secret")
ADMIN_ID = 264354988

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не встановлено. Додайте його в .env")


class FormStates(StatesGroup):
    name = State()
    age = State()
    citizenship = State()
    city = State()
    of_pages = State()
    of_stats = State()
    content_18 = State()
    taboo = State()
    toys_18 = State()
    phone_model = State()
    blogger_lamp = State()
    led_tapes = State()
    apartment = State()
    hours_per_day = State()
    tiktok_reels = State()
    salary_expectation = State()
    start_date = State()
    capabilities = State()


FORM_FIELDS = [
    ("Ім'я", "name"),
    ("Вік", "age"),
    ("Громадянство", "citizenship"),
    ("Місто проживання", "city"),
    ("Зареєстровані сторінки на OF", "of_pages"),
    ("Який актив/скільки фанів, якщо є сторінки OF", "of_stats"),
    ("🔞 Контент 18+", "content_18"),
    ("🔞 Табу", "taboo"),
    ("🔞 Іграшки 18+", "toys_18"),
    ("📸 Модель телефону", "phone_model"),
    ("📸 Блогерська лампа", "blogger_lamp"),
    ("📸 LED-стрічки", "led_tapes"),
    ("📸 Квартира (гарна/середня/погана)", "apartment"),
    ("❓ Скільки часу готова приділяти роботі на день?", "hours_per_day"),
    ("❓ Чи будеш записувати TikTok та Reels?", "tiktok_reels"),
    ("❓ Яку зарплату очікуєш отримувати на місяць?", "salary_expectation"),
    ("❓ Коли готова приступити до роботи?", "start_date"),
]

CAPABILITIES = [
    "Відео з іграшками (дилдо/вібратор)",
    "Крупний план піхви",
    "Крупний план сідниць",
    "Крупний план грудей",
    "Крупний план стоп/ніг",
    "Мастурбація пальцями",
    "Мастурбація вібратором",
    "Мастурбація дилдо",
    "Еротична нижня білизна",
    "Колготки/панчохи",
    "Мінет з іграшкою",
    "Проникнення в анал",
    "Подвійне проникнення",
    "Сквирт",
    "Парний контент",
]

FAQ_TEXT = (
    "❓ <b>Що мені потрібно робити як моделі?</b>\n"
    "Ваше ключове завдання це регулярно створювати контент за нашими технічними брифами. "
    "Стратегія, трафік, комунікація, менеджмент і монетизація залишаються на стороні агенції.\n\n"
    "❓ <b>Чи потрібен досвід?</b>\n"
    "Досвід бажаний, але не є обов'язковою умовою. Для нас важливі дисципліна, відкритість до системної "
    "роботи та готовність дотримуватися рекомендацій команди.\n\n"
    "❓ <b>Як часто потрібно знімати контент?</b>\n"
    "Частота залежить від обраної стратегії, платформи та темпу росту. Ми задаємо чіткий ритм і формат так, "
    "щоб навантаження було прогнозованим.\n\n"
    "❓ <b>Що саме бере на себе агенція?</b>\n"
    "Ми ведемо стратегію, позиціонування, traffic management, контент-планування, управління акаунтом, "
    "fan communication, аналітику та системи монетизації.\n\n"
    "❓ <b>Як подати заявку?</b>\n"
    "Заповніть форму нижче, або одразу напишіть HR-менеджерці в Telegram чи перейдіть у бот для анкет. "
    "Ми переглядаємо заявки вручну.\n\n"
    "❓ <b>Чи захищена моя приватність?</b>\n"
    "Так. Конфіденційність, контроль доступів і акуратна комунікація є базовою частиною нашої операційної моделі."
)


def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Анкета", callback_data="menu_form")
    kb.button(text="FAQ", callback_data="menu_faq")
    kb.button(text="Зворотній зв'язок", url="https://t.me/gimmemo_hr")
    kb.button(text="Сайт", url="https://gimmemo.fun")
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def capability_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for idx, item in enumerate(CAPABILITIES):
        mark = "✅" if str(idx) in selected else "❌"
        kb.button(text=f"{mark} {item}", callback_data=f"cap_toggle:{idx}")
    kb.button(text="Готово", callback_data="cap_done")
    kb.adjust(1)
    return kb.as_markup()


def build_form_message(data: dict) -> str:
    lines = ["<b>Нова анкета</b>", ""]
    for title, key in FORM_FIELDS:
        value = escape(str(data.get(key, "-")))
        lines.append(f"<b>{escape(title)}:</b> {value}")

    lines.append("")
    lines.append("<b>Готовність за форматами:</b>")
    capabilities = data.get("capabilities", {})
    for item in CAPABILITIES:
        status = capabilities.get(item, "❌")
        lines.append(f"{status} {escape(item)}")

    lines.append("")
    user = data.get("_user_meta", {})
    lines.append(
        f"<i>Від користувача:</i> id={user.get('id')} | username=@{escape(user.get('username', '-'))} "
        f"| ім'я={escape(user.get('full_name', '-'))}"
    )
    return "\n".join(lines)


bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Вітаю! Оберіть потрібний розділ у меню нижче:",
        reply_markup=main_menu(),
    )


@dp.callback_query(F.data == "menu_faq")
async def faq_handler(callback, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(FAQ_TEXT, reply_markup=main_menu())
    await callback.answer()


@dp.callback_query(F.data == "menu_form")
async def form_start(callback, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(FormStates.name)
    await state.update_data(
        _user_meta={
            "id": callback.from_user.id,
            "username": callback.from_user.username or "-",
            "full_name": callback.from_user.full_name or "-",
        }
    )
    await callback.message.answer("Ім'я:")
    await callback.answer()


async def _set_next_state(message: Message, state: FSMContext, key: str, next_state: State, prompt: str) -> None:
    await state.update_data(**{key: message.text.strip()})
    await state.set_state(next_state)
    await message.answer(prompt)


@dp.message(FormStates.name)
async def form_name(message: Message, state: FSMContext) -> None:
    await _set_next_state(message, state, "name", FormStates.age, "Вік:")


@dp.message(FormStates.age)
async def form_age(message: Message, state: FSMContext) -> None:
    await _set_next_state(message, state, "age", FormStates.citizenship, "Громадянство:")


@dp.message(FormStates.citizenship)
async def form_citizenship(message: Message, state: FSMContext) -> None:
    await _set_next_state(message, state, "citizenship", FormStates.city, "Місто проживання:")


@dp.message(FormStates.city)
async def form_city(message: Message, state: FSMContext) -> None:
    await _set_next_state(
        message, state, "city", FormStates.of_pages, "Зареєстровані сторінки на OF:"
    )


@dp.message(FormStates.of_pages)
async def form_of_pages(message: Message, state: FSMContext) -> None:
    await _set_next_state(
        message,
        state,
        "of_pages",
        FormStates.of_stats,
        "Який актив/скільки фанів, якщо є сторінки OF:",
    )


@dp.message(FormStates.of_stats)
async def form_of_stats(message: Message, state: FSMContext) -> None:
    await _set_next_state(message, state, "of_stats", FormStates.content_18, "🔞 Контент 18+:")


@dp.message(FormStates.content_18)
async def form_content_18(message: Message, state: FSMContext) -> None:
    await _set_next_state(message, state, "content_18", FormStates.taboo, "🔞 Табу:")


@dp.message(FormStates.taboo)
async def form_taboo(message: Message, state: FSMContext) -> None:
    await _set_next_state(message, state, "taboo", FormStates.toys_18, "🔞 Іграшки 18+:")


@dp.message(FormStates.toys_18)
async def form_toys(message: Message, state: FSMContext) -> None:
    await _set_next_state(message, state, "toys_18", FormStates.phone_model, "📸 Модель телефону:")


@dp.message(FormStates.phone_model)
async def form_phone(message: Message, state: FSMContext) -> None:
    await _set_next_state(message, state, "phone_model", FormStates.blogger_lamp, "📸 Блогерська лампа:")


@dp.message(FormStates.blogger_lamp)
async def form_lamp(message: Message, state: FSMContext) -> None:
    await _set_next_state(message, state, "blogger_lamp", FormStates.led_tapes, "📸 LED-стрічки:")


@dp.message(FormStates.led_tapes)
async def form_led(message: Message, state: FSMContext) -> None:
    await _set_next_state(
        message,
        state,
        "led_tapes",
        FormStates.apartment,
        "📸 Квартира (гарна/середня/погана):",
    )


@dp.message(FormStates.apartment)
async def form_apartment(message: Message, state: FSMContext) -> None:
    await _set_next_state(
        message,
        state,
        "apartment",
        FormStates.hours_per_day,
        "❓ Скільки часу готова приділяти роботі на день?",
    )


@dp.message(FormStates.hours_per_day)
async def form_hours(message: Message, state: FSMContext) -> None:
    await _set_next_state(
        message,
        state,
        "hours_per_day",
        FormStates.tiktok_reels,
        "❓ Чи будеш записувати TikTok та Reels?",
    )


@dp.message(FormStates.tiktok_reels)
async def form_tiktok(message: Message, state: FSMContext) -> None:
    await _set_next_state(
        message,
        state,
        "tiktok_reels",
        FormStates.salary_expectation,
        "❓ Яку зарплату очікуєш отримувати на місяць?",
    )


@dp.message(FormStates.salary_expectation)
async def form_salary(message: Message, state: FSMContext) -> None:
    await _set_next_state(
        message,
        state,
        "salary_expectation",
        FormStates.start_date,
        "❓ Коли готова приступити до роботи?",
    )


@dp.message(FormStates.start_date)
async def form_start_date(message: Message, state: FSMContext) -> None:
    await state.update_data(start_date=message.text.strip(), capabilities={})
    await state.set_state(FormStates.capabilities)
    await message.answer(
        "Тепер для кожного пункту натисніть, щоб перемкнути між ✅ та ❌. "
        "Коли завершите, натисніть «Готово».",
        reply_markup=capability_keyboard(set()),
    )


@dp.callback_query(FormStates.capabilities, F.data.startswith("cap_toggle:"))
async def capability_toggle(callback, state: FSMContext) -> None:
    idx = int(callback.data.split(":")[1])
    item = CAPABILITIES[idx]
    data = await state.get_data()
    cap = data.get("capabilities", {})
    current = cap.get(item, "❌")
    cap[item] = "✅" if current == "❌" else "❌"
    await state.update_data(capabilities=cap)

    selected = {str(i) for i, c in enumerate(CAPABILITIES) if cap.get(c) == "✅"}
    await callback.message.edit_reply_markup(reply_markup=capability_keyboard(selected))
    await callback.answer()


@dp.callback_query(FormStates.capabilities, F.data == "cap_done")
async def capability_done(callback, state: FSMContext) -> None:
    data = await state.get_data()
    text = build_form_message(data)

    await bot.send_message(ADMIN_ID, text)
    await callback.message.answer(
        "Дякуємо! Анкету надіслано менеджеру ✅",
        reply_markup=main_menu(),
    )
    await state.clear()
    await callback.answer()


@dp.message()
async def fallback_handler(message: Message) -> None:
    await message.answer("Оберіть дію в меню:", reply_markup=main_menu())


async def main() -> None:
    if WEBHOOK_BASE_URL:
        webhook_url = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url, secret_token=WEBHOOK_SECRET)

        app = web.Application()
        SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=WEBHOOK_SECRET,
        ).register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)

        port = int(os.getenv("PORT", "8080"))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=port)
        await site.start()
        logging.info("Webhook mode started on port %s", port)

        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        finally:
            await bot.delete_webhook()
            await runner.cleanup()
    else:
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
