import asyncio
import logging
import os
import re
from datetime import date, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# ТВОИ ДАННЫЕ (уже вставлены!)
BOTTOKEN = os.getenv("8747315107:AAGUkCUbbQvZ24uxKPWSmceQOF8Plf67s-g")
YOURCHATID = int(os.getenv(901984475))

# Города Мурманской области
CITIES = [
    "Мурманск", "Апатиты", "Североморск", "Мончегорск", "Оленегорск",
    "Кандалакша", "Кировск", "Полярные Зори", "Заозёрск", "Кола"
]

# Услуги
SERVICES = ["Двери", "Окна", "Потолок", "Утепление балконов", "Жалюзи"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class Form(StatesGroup):
    name = State()
    city = State()
    phone = State()
    service = State()
    date_consult = State()


@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    kb = [
        [KeyboardButton(text="🚀 Начать заявку")],
        [KeyboardButton(text="ℹ️ О компании")]
    ]
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
        "👋 Привет! Добро пожаловать в ФИС51! 🏠\n\n"
        "Мы предоставляем услуги:\n"
        "• Двери и окна\n"
        "• Потолки и жалюзи\n"
        "• Утепление балконов\n\n"
        "Нажми '🚀 Начать заявку' 👇",
        reply_markup=markup
    )


@dp.message(F.text == "🚀 Начать заявку")
async def process_name(message: Message, state: FSMContext):
    await message.answer("👤 Как Вас зовут?")
    await state.set_state(Form.name)


@dp.message(StateFilter(Form.name))
async def process_city(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    kb = [[KeyboardButton(text=city)] for city in CITIES[:6]] + [[KeyboardButton(text="Другой город")]]
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer(
        "🏙 Из какого города Мурманской области ты?\n"
        "Выбери или напиши свой:",
        reply_markup=markup
    )
    await state.set_state(Form.city)


@dp.message(StateFilter(Form.city))
async def process_phone(message: Message, state: FSMContext):
    city = message.text.strip()
    await state.update_data(city=city)

    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer(
        "📱 Отправь свой номер телефона для связи:\n"
        "• Кнопка ниже ИЛИ\n"
        "• Напиши вручную: +7XXXXXXXXXX",
        reply_markup=markup
    )
    await state.set_state(Form.phone)


@dp.message(StateFilter(Form.phone), F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await process_service(message, state)


@dp.message(StateFilter(Form.phone))
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if re.match(r'^\+7\d{10}$', phone):
        await state.update_data(phone=phone)
        await process_service(message, state)
    else:
        await message.answer(
            "❌ Неверный формат!\n"
            "Правильно: +79991234567\n\n"
            "Попробуй еще раз:"
        )
        return


async def process_service(message: Message, state: FSMContext):
    kb = [[KeyboardButton(text=srv)] for srv in SERVICES]
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer(
        "🔨 Какая услуга тебе нужна? Выбери:",
        reply_markup=markup
    )
    await state.set_state(Form.service)


@dp.message(StateFilter(Form.service))
async def process_date_select(message: Message, state: FSMContext):
    await state.update_data(service=message.text.strip())

    # 7 кнопок дат (сегодня + 6 дней)
    keyboard = []
    for i in range(7):
        current_date = date.today() + timedelta(days=i)
        date_str = current_date.strftime("%d.%m.%Y")
        day_name = current_date.strftime("%A")
        day_names = {
            "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
            "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
        }
        date_label = current_date.strftime("%d") + " " + day_names.get(day_name, day_name)
        keyboard.append([KeyboardButton(text=f"📅 {date_label} ({date_str})")])

    markup = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "📅 Выбери удобную дату для консультации:\n"
        "(сегодня + неделя вперед)",
        reply_markup=markup
    )
    await state.set_state(Form.date_consult)


@dp.message(StateFilter(Form.date_consult))
async def send_application(message: Message, state: FSMContext):
    data = await state.get_data()
    app_text = (
        f"🆕 НОВАЯ ЗАЯВКА ФИС51!\n\n"
        f"👤 Имя: {data['name']}\n"
        f"🏙 Город: {data['city']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"🔨 Услуга: {data['service']}\n"
        f"📅 Консультация: {message.text}\n"
        f"🕐 {date.today().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"🚀 Срочно обработать!"
    )

    try:
        await bot.send_message(YOUR_CHAT_ID, app_text)
        await message.answer(
            "✅ Заявка отправлена!\n"
            "Менеджер свяжется в течение часа! 😊\n\n"
            "Спасибо за обращение в ФИС51! 🏠",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🚀 Новая заявка")]],
                resize_keyboard=True
            )
        )
    except Exception as e:
        await message.answer("❌ Ошибка отправки. Попробуй еще раз.")
        print(f"Ошибка: {e}")

    await state.clear()


@dp.message(F.text == "🚀 Новая заявка")
async def new_application(message: Message, state: FSMContext):
    await start_handler(message, state)


@dp.message(F.text == "ℹ️ О компании")
async def about_company(message: Message):
    await message.answer(
        "🏠 ФИС51 — надежные окна, двери и отделка в Мурманской области!\n\n"
        "✅ 10+ лет опыта\n"
        "✅ Гарантия на работы\n"
        "✅ Бесплатный замер\n\n"
        "🚀 Начать заявку?"
    )


async def main():
    print("🤖 Бот ФИС51 запущен на Render!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
