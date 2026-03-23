import asyncio
import logging
import os
from html import escape

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8735115748:AAEA2i6UIvF3ERxZHz_OSMT23kvmM9vGbyo"
WEBHOOK_BASE_URL = "https://gimmemo.onrender.com"
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

FORM_FLOW = [
    (FormStates.name, "name", "Ім'я:", None),
    (FormStates.age, "age", "Вік:", None),
    (FormStates.citizenship, "citizenship", "Громадянство:", None),
    (FormStates.city, "city", "Місто проживання:", None),
    (FormStates.of_pages, "of_pages", "Зареєстровані сторінки на OF:", None),
    (
        FormStates.of_stats,
        "of_stats",
        "Який актив/скільки фанів, якщо є сторінки OF:",
        None,
    ),
    (FormStates.toys_18, "toys_18", "🔞 Іграшки 18+:", None),
    (FormStates.phone_model, "phone_model", "📸 Модель телефону:", None),
    (
        FormStates.blogger_lamp,
        "blogger_lamp",
        "📸 Блогерська лампа:",
        [("✅ Так", "Так"), ("❌ Ні", "Ні")],
    ),
    (
        FormStates.led_tapes,
        "led_tapes",
        "📸 LED-стрічки:",
        [("✅ Так", "Так"), ("❌ Ні", "Ні")],
    ),
    (
        FormStates.apartment,
        "apartment",
        "📸 Квартира:",
        [("✨ Гарна", "гарна"), ("👌 Середня", "середня"), ("⚠️ Погана", "погана")],
    ),
    (
        FormStates.hours_per_day,
        "hours_per_day",
        "❓ Скільки часу готова приділяти роботі на день?",
        None,
    ),
    (
        FormStates.tiktok_reels,
        "tiktok_reels",
        "❓ Чи будеш записувати TikTok та Reels?",
        [("✅ Так", "Так"), ("❌ Ні", "Ні")],
    ),
    (
        FormStates.salary_expectation,
        "salary_expectation",
        "❓ Яку зарплату очікуєш отримувати на місяць?",
        None,
    ),
    (
        FormStates.start_date,
        "start_date",
        "❓ Коли готова приступити до роботи?",
        None,
    ),
]

STATE_TO_STEP = {state.state: (state, key, prompt, options) for state, key, prompt, options in FORM_FLOW}
STATE_ORDER = [state.state for state, _, _, _ in FORM_FLOW]
STATE_TO_NEXT = {STATE_ORDER[i]: (STATE_ORDER[i + 1] if i + 1 < len(STATE_ORDER) else None) for i in range(len(STATE_ORDER))}
STATE_NAME_TO_OBJ = {state.state: state for state, _, _, _ in FORM_FLOW}


def normalize_answer(text: str) -> str:
    return text.strip().lower().replace(".", "").replace("!", "").replace("?", "")


def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Анкета", callback_data="menu_form")
    kb.button(text="❓ FAQ", callback_data="menu_faq")
    kb.button(text="💬 Зворотний зв'язок", url="https://t.me/gimmemo_hr")
    kb.button(text="🌐 Сайт", url="https://gimmemo.fun")
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def faq_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Головне меню", callback_data="menu_home")
    kb.adjust(1)
    return kb.as_markup()


def form_nav_keyboard(
    state_key: str,
    options: list[tuple[str, str]] | None = None,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if options:
        for label, value in options:
            kb.button(text=label, callback_data=f"quick_answer:{state_key}:{value}")
    kb.button(text="⬅️ Назад", callback_data="form_back")
    kb.button(text="🏠 Головне меню", callback_data="form_home")
    kb.adjust(*(1 for _ in (options or [])), 2)
    return kb.as_markup()


def capability_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for idx, item in enumerate(CAPABILITIES):
        mark = "✅" if str(idx) in selected else "❌"
        kb.button(text=f"{mark} {item}", callback_data=f"cap_toggle:{idx}")
    kb.button(text="✅ Готово", callback_data="cap_done")
    kb.button(text="⬅️ Назад", callback_data="form_back")
    kb.button(text="🏠 Головне меню", callback_data="form_home")
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
    await callback.message.answer(FAQ_TEXT, reply_markup=faq_menu())
    await callback.answer()


@dp.callback_query(F.data == "menu_home")
async def home_from_submenus(callback, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Оберіть потрібний розділ:", reply_markup=main_menu())
    await callback.answer()


@dp.callback_query(F.data == "menu_form")
async def form_start(callback, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(
        _history=[],
        _user_meta={
            "id": callback.from_user.id,
            "username": callback.from_user.username or "-",
            "full_name": callback.from_user.full_name or "-",
        }
    )
    await ask_step(callback.message, state, FormStates.name)
    await callback.answer()


async def ask_step(message: Message, state: FSMContext, step_state: State) -> None:
    _, key, prompt, options = STATE_TO_STEP[step_state.state]
    await state.set_state(step_state)
    await message.answer(prompt, reply_markup=form_nav_keyboard(key, options))


async def go_next(message: Message, state: FSMContext, current_state_name: str) -> None:
    data = await state.get_data()
    history = data.get("_history", [])
    history.append(current_state_name)
    await state.update_data(_history=history)

    next_state_name = STATE_TO_NEXT.get(current_state_name)
    if not next_state_name:
        await state.update_data(capabilities={})
        await state.set_state(FormStates.capabilities)
        await message.answer(
            "Тепер для кожного пункту натисніть, щоб перемкнути між ✅ та ❌. "
            "Коли завершите, натисніть «Готово».",
            reply_markup=capability_keyboard(set()),
        )
        return

    await ask_step(message, state, STATE_NAME_TO_OBJ[next_state_name])


@dp.message(StateFilter(*[STATE_NAME_TO_OBJ[name] for name in STATE_ORDER]))
async def form_text_answers(message: Message, state: FSMContext) -> None:
    current_state_name = await state.get_state()
    if current_state_name is None:
        return
    _, key, _, options = STATE_TO_STEP[current_state_name]
    user_text = (message.text or "").strip()
    if not user_text:
        await message.answer("Введіть відповідь текстом або натисніть кнопку нижче.")
        return

    if options:
        allowed_map = {normalize_answer(value): value for _, value in options}
        normalized = normalize_answer(user_text)
        if normalized not in allowed_map:
            allowed_hints = ", ".join(value for _, value in options)
            await message.answer(
                f"Будь ласка, оберіть один із варіантів: {allowed_hints}.",
                reply_markup=form_nav_keyboard(key, options),
            )
            return
        await state.update_data(**{key: allowed_map[normalized]})
    else:
        await state.update_data(**{key: user_text})
    await go_next(message, state, current_state_name)


@dp.callback_query(F.data.startswith("quick_answer:"))
async def form_quick_answers(callback, state: FSMContext) -> None:
    current_state_name = await state.get_state()
    if current_state_name is None or current_state_name not in STATE_TO_STEP:
        await callback.answer()
        return

    _, key, _, _ = STATE_TO_STEP[current_state_name]
    _, answer_key, value = callback.data.split(":", 2)
    if key != answer_key:
        await callback.answer("Застаріла кнопка", show_alert=False)
        return

    await state.update_data(**{key: value})
    await callback.answer()
    await go_next(callback.message, state, current_state_name)


@dp.message(FormStates.capabilities)
async def capabilities_text_guard(message: Message) -> None:
    await message.answer("На цьому кроці використовуйте кнопки ✅/❌ та «✅ Готово».")


@dp.callback_query(F.data == "form_back")
async def form_back(callback, state: FSMContext) -> None:
    current_state_name = await state.get_state()
    if current_state_name is None:
        await callback.answer("Анкета не активна", show_alert=False)
        return

    data = await state.get_data()
    history = data.get("_history", [])

    if current_state_name == FormStates.capabilities.state and history:
        prev_state_name = history.pop()
        await state.update_data(_history=history)
        await ask_step(callback.message, state, STATE_NAME_TO_OBJ[prev_state_name])
        await callback.answer()
        return

    if not history:
        if current_state_name in STATE_NAME_TO_OBJ:
            await callback.message.answer("Це перше питання анкети.")
            await ask_step(callback.message, state, STATE_NAME_TO_OBJ[current_state_name])
        else:
            await callback.message.answer("Це перше питання анкети.")
        await callback.answer()
        return

    prev_state_name = history.pop()
    await state.update_data(_history=history)
    await ask_step(callback.message, state, STATE_NAME_TO_OBJ[prev_state_name])
    await callback.answer()


@dp.callback_query(F.data == "form_home")
async def form_home(callback, state: FSMContext) -> None:
    current_state_name = await state.get_state()
    if current_state_name is None:
        await callback.answer("Анкета не активна", show_alert=False)
        return
    await state.clear()
    await callback.message.answer("Повернулися у головне меню.", reply_markup=main_menu())
    await callback.answer()


@dp.callback_query(FormStates.capabilities, F.data.startswith("cap_toggle:"))
async def capability_toggle(callback, state: FSMContext) -> None:
    try:
        idx = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("Некоректна кнопка", show_alert=False)
        return
    if idx < 0 or idx >= len(CAPABILITIES):
        await callback.answer("Некоректна кнопка", show_alert=False)
        return

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

