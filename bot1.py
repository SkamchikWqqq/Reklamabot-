import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ===================== НАСТРОЙКИ =====================
BOT_TOKEN = "8678287845:AAGtdxy4gxxBWCe9y4aPTRGs8sjHFmNNtto"

# Администраторы (username без @)
ADMINS = ["cunpar", "parksback"]

# Каналы для обязательной подписки (начальные)
# Формат: {"id": -100xxxxxxxxx, "link": "https://t.me/channel", "title": "Название"}
REQUIRED_CHANNELS = [
    # Добавьте ваши каналы здесь, например:
    # {"id": -1001234567890, "link": "https://t.me/yourchannel", "title": "Канал 1"},
]

# ===================== FSM СОСТОЯНИЯ =====================
class SnosStates(StatesGroup):
    waiting_username = State()
    waiting_type = State()
    processing = State()

class AddChannelStates(StatesGroup):
    waiting_channel_id = State()
    waiting_channel_link = State()
    waiting_channel_title = State()

# ===================== ИНИЦИАЛИЗАЦИЯ =====================
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===================== КЛАВИАТУРЫ =====================
def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="💀 Zn#s", callback_data="snos")],
        [InlineKeyboardButton(text="💫 Канал создателя", callback_data="donate")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_channel")])
        buttons.append([InlineKeyboardButton(text="🗑 Удалить канал", callback_data="delete_channel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def snos_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐  Zn#s сессий", callback_data="snos_sessions")],
        [InlineKeyboardButton(text="⚠️  Zn#s жалобами", callback_data="snos_reports")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_menu")],
    ])

def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_menu")]
    ])

def subscribe_keyboard(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 {ch['title']}", url=ch['link'])])
    buttons.append([InlineKeyboardButton(text="📣 Подпишись на канал разработчика бота", url="https://t.me/leackShop")])
    buttons.append([InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def delete_channel_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for i, ch in enumerate(REQUIRED_CHANNELS):
        buttons.append([InlineKeyboardButton(text=f"❌ {ch['title']}", callback_data=f"del_ch_{i}")])
    buttons.append([InlineKeyboardButton(text="◀️ В меню", callback_data="back_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ===================== ПРОВЕРКА ПОДПИСКИ =====================
async def check_subscriptions(user_id: int) -> list:
    """Возвращает список каналов, на которые НЕ подписан пользователь"""
    not_subscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(channel["id"], user_id)
            if member.status in ("left", "kicked", "banned"):
                not_subscribed.append(channel)
        except Exception:
            not_subscribed.append(channel)
    return not_subscribed

def is_admin(username: str) -> bool:
    return username and username.lower() in [a.lower() for a in ADMINS]

async def send_welcome_with_photo(target, text: str, keyboard=None):
    """Отправляет сообщение с фото paranoia_attack.png"""
    try:
        photo = FSInputFile("paranoia_attack.png")
        if keyboard:
            await target.answer_photo(photo=photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await target.answer_photo(photo=photo, caption=text, parse_mode="HTML")
    except Exception:
        # Если фото не найдено — отправляем без фото
        if keyboard:
            await target.answer(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await target.answer(text, parse_mode="HTML")

# ===================== СТАРТ =====================
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or ""
    admin = is_admin(username)

    # Проверка подписки
    not_subscribed = await check_subscriptions(user_id)

    if not_subscribed:
        text = (
            "⛔️ <b>Для использования бота необходимо подписаться на все каналы!</b>\n\n"
            "Подпишитесь на каналы ниже и нажмите кнопку ✅"
        )
        try:
            photo = FSInputFile("paranoia_attack.png")
            await message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=subscribe_keyboard(not_subscribed),
                parse_mode="HTML"
            )
        except Exception:
            await message.answer(text, reply_markup=subscribe_keyboard(not_subscribed), parse_mode="HTML")
        return

    # Подписан — показываем меню
    text = (
        "💀 <b>Д0бро пожаловать в Zn#s3r</b>\n\n"
        "Выберите пункт:"
    )
    try:
        photo = FSInputFile("paranoia_attack.png")
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=main_menu_keyboard(admin),
            parse_mode="HTML"
        )
    except Exception:
        await message.answer(text, reply_markup=main_menu_keyboard(admin), parse_mode="HTML")

# ===================== ПРОВЕРКА ПОДПИСКИ (кнопка) =====================
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    username = callback.from_user.username or ""
    admin = is_admin(username)

    not_subscribed = await check_subscriptions(user_id)

    if not_subscribed:
        await callback.answer("❌ Вы ещё не подписались на все каналы!", show_alert=True)
        return

    text = (
        "💀 <b>Д0бро пожаловать в Zn#s3r</b>\n\n"
        "Выберите пункт:"
    )
    await callback.message.edit_caption(caption=text, reply_markup=main_menu_keyboard(admin), parse_mode="HTML")
    await callback.answer("✅ Подписка подтверждена!")

# ===================== МЕНЮ =====================
@dp.callback_query(F.data == "back_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    username = callback.from_user.username or ""
    admin = is_admin(username)
    text = (
        "💀 <b>Д0бро пожаловать в Zn#s3r</b>\n\n"
        "Выберите пункт:"
    )
    try:
        await callback.message.edit_caption(caption=text, reply_markup=main_menu_keyboard(admin), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=main_menu_keyboard(admin), parse_mode="HTML")
    await callback.answer()

# ===================== СНОС =====================
@dp.callback_query(F.data == "snos")
async def snos_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SnosStates.waiting_username)
    text = (
        "💀 <b> Zn#s3r — Запуск</b>\n\n"
        "Отправьте <code>@username</code> человека:"
    )
    try:
        await callback.message.edit_caption(caption=text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.message(SnosStates.waiting_username)
async def snos_get_username(message: Message, state: FSMContext):
    username = message.text.strip()
    await state.update_data(target=username)
    await state.set_state(SnosStates.waiting_type)
    text = (
        f"🎯 <b>Цель:</b> <code>{username}</code>\n\n"
        "Выберите тип  Zn#sа:"
    )
    await message.answer(text, reply_markup=snos_type_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data.in_({"snos_sessions", "snos_reports"}))
async def snos_process(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target = data.get("target", "unknown")
    snos_type = "🔐 Zn#s сессий" if callback.data == "snos_sessions" else "⚠️ Zn#s жалобами"

    await state.set_state(SnosStates.processing)

    text = (
        f"⚙️ <b>Запуск Zn#sа...</b>\n\n"
        f"🎯 Цель: <code>{target}</code>\n"
        f"📌 Тип: {snos_type}\n\n"
        f"<i>Инициализация модулей...</i>"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

    # Имитация процесса
    messages_list = [
        "🔄 Подключение к серверам...",
        "🔍 Поиск цели в базе данных...",
        "🛡️ Обход защиты...",
        "💥 Выполнение операции...",
        "📡 Отправка запросов...",
        "⚡️ Финальная стадия...",
    ]

    for i, msg in enumerate(messages_list, 1):
        await asyncio.sleep(random.uniform(1.0, 2.0))
        progress = "▓" * i + "░" * (len(messages_list) - i)
        text = (
            f"⚙️ <b>Zn#s в процессе...</b>\n\n"
            f"🎯 Цель: <code>{target}</code>\n"
            f"📌 Тип: {snos_type}\n\n"
            f"[{progress}] {i}/{len(messages_list)}\n"
            f"<i>{msg}</i>"
        )
        await callback.message.edit_text(text, parse_mode="HTML")

    await asyncio.sleep(1.5)

    final_text = (
        f"✅ <b>Человек успешно sне сен!</b>\n\n"
        f"🎯 Цель: <code>{target}</code>\n"
        f"📌 Тип: {snos_type}\n\n"
        f"Спасибо за использование бота! 🚀"
    )
    await callback.message.edit_text(
        final_text,
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML"
    )
    await state.clear()

# ===================== ПОЖЕРТВОВАТЬ =====================
@dp.callback_query(F.data == "donate")
async def donate(callback: CallbackQuery):
    text = "Для поддержки Разработчика бота, подпишись на его личный канал =)"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📣 Подпишись на канал разработчика бота", url="https://t.me/leackShop")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_menu")],
    ])
    try:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
# ===================== О БОТЕ =====================
@dp.callback_query(F.data == "about")
async def about(callback: CallbackQuery):
    text = "🤖 <b>О боте</b>\n\nБот создан благодаря @cunpar"
    try:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()

# ===================== ДОБАВЛЕНИЕ КАНАЛА (ТОЛЬКО АДМИНЫ) =====================
@dp.callback_query(F.data == "add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username or ""
    if not is_admin(username):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    await state.set_state(AddChannelStates.waiting_channel_id)
    text = (
        "➕ <b>Добавление канала</b>\n\n"
        "Шаг 1/3: Отправьте <b>ID канала</b>\n"
        "<i>Пример: -1001234567890</i>\n\n"
        "⚠️ Не забудьте добавить бота в администраторы канала!"
    )
    await callback.message.answer(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.message(AddChannelStates.waiting_channel_id)
async def add_channel_id(message: Message, state: FSMContext):
    username = message.from_user.username or ""
    if not is_admin(username):
        return
    try:
        channel_id = int(message.text.strip())
        await state.update_data(channel_id=channel_id)
        await state.set_state(AddChannelStates.waiting_channel_link)
        await message.answer(
            "Шаг 2/3: Отправьте <b>ссылку на канал</b>\n<i>Пример: https://t.me/yourchannel</i>",
            reply_markup=back_to_menu_keyboard(), parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число, например: -1001234567890")

@dp.message(AddChannelStates.waiting_channel_link)
async def add_channel_link(message: Message, state: FSMContext):
    username = message.from_user.username or ""
    if not is_admin(username):
        return
    link = message.text.strip()
    await state.update_data(channel_link=link)
    await state.set_state(AddChannelStates.waiting_channel_title)
    await message.answer(
        "Шаг 3/3: Отправьте <b>название канала</b>\n<i>Пример: Мой канал</i>",
        reply_markup=back_to_menu_keyboard(), parse_mode="HTML"
    )

@dp.message(AddChannelStates.waiting_channel_title)
async def add_channel_title(message: Message, state: FSMContext):
    username = message.from_user.username or ""
    if not is_admin(username):
        return
    title = message.text.strip()
    data = await state.get_data()

    new_channel = {
        "id": data["channel_id"],
        "link": data["channel_link"],
        "title": title
    }
    REQUIRED_CHANNELS.append(new_channel)
    await state.clear()

    await message.answer(
        f"✅ <b>Канал успешно добавлен!</b>\n\n"
        f"📢 <b>{title}</b>\n"
        f"🆔 <code>{data['channel_id']}</code>\n"
        f"🔗 {data['channel_link']}\n\n"
        f"Всего каналов для подписки: <b>{len(REQUIRED_CHANNELS)}</b>",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML"
    )

# ===================== УДАЛЕНИЕ КАНАЛА (ТОЛЬКО АДМИНЫ) =====================
@dp.callback_query(F.data == "delete_channel")
async def delete_channel_menu(callback: CallbackQuery):
    username = callback.from_user.username or ""
    if not is_admin(username):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    if not REQUIRED_CHANNELS:
        await callback.answer("📭 Список каналов пуст!", show_alert=True)
        return

    text = "🗑 <b>Какой канал желаете удалить?</b>"
    try:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=delete_channel_keyboard(),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(text, reply_markup=delete_channel_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("del_ch_"))
async def delete_channel_confirm(callback: CallbackQuery):
    username = callback.from_user.username or ""
    if not is_admin(username):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        index = int(callback.data.split("_")[2])
        if 0 <= index < len(REQUIRED_CHANNELS):
            removed = REQUIRED_CHANNELS.pop(index)
            text = (
                f"✅ <b>Канал удалён!</b>\n\n"
                f"📢 <b>{removed['title']}</b>\n"
                f"🆔 <code>{removed['id']}</code>\n\n"
                f"Осталось каналов: <b>{len(REQUIRED_CHANNELS)}</b>"
            )
            try:
                await callback.message.edit_caption(
                    caption=text,
                    reply_markup=back_to_menu_keyboard(),
                    parse_mode="HTML"
                )
            except Exception:
                await callback.message.answer(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
        else:
            await callback.answer("❌ Канал не найден!", show_alert=True)
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка при удалении!", show_alert=True)

    await callback.answer()

# ===================== ЗАПУСК =====================
async def main():
    print("🤖 Zn#s3r Bot запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())