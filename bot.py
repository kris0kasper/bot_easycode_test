# bot.py
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import re
from datetime import datetime
import asyncio

from storage import add_birthday, get_user_birthdays, delete_birthday

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Вставьте ваш токен от @BotFather
BOT_TOKEN = "8090283397:AAHUyO6QAb_4EjACWCP2OuNqhQKAAr_b4-4"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Валидация даты ---
def validate_date(date_str):
    """Проверяет формат YYYY-MM-DD и корректность даты."""
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# --- Команды ---
@dp.message(Command('start', 'help'))
async def send_welcome(message: types.Message):
    help_text = (
        "🎂 Бот для хранения дней рождения друзей!\n\n"
        "Команды:\n"
        "/add <Имя> <ГГГГ-ММ-ДД> — добавить день рождения\n"
        "/delete <Имя> — удалить запись\n"
        "/list — показать все дни рождения\n"
        "/help — показать эту подсказку\n\n"
        "Пример: /add Анна 1990-05-15"
    )
    await message.answer(help_text)

@dp.message(Command('add'))
async def add_birthday_handler(message: types.Message):
    text = message.text.strip()
    if not text:
        await message.answer("❌ Неверный формат.\nИспользуйте: /add <Имя> <ГГГГ-ММ-ДД>")
        return

    # Удаляем команду из текста (например, "/add " -> оставляем только аргументы)
    command = "/add"
    args_text = text[len(command):].strip() if text.startswith(command) else text
    if not args_text:
        await message.answer("❌ Неверный формат.\nИспользуйте: /add <Имя> <ГГГГ-ММ-ДД>")
        return

    # Разбиваем оставшийся текст на имя и дату
    parts = args_text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Неверный формат.\nИспользуйте: /add <Имя> <ГГГГ-ММ-ДД>")
        return

    name = parts[0].strip()
    date_str = parts[1].strip()

    if not name or not date_str:
        await message.answer("❌ Имя и дата не могут быть пустыми.")
        return

    if not validate_date(date_str):
        await message.answer("❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД, например: 1990-05-15")
        return

    add_birthday(message.from_user.id, name, date_str)
    await message.answer(f"✅ Добавлено: {name} — {date_str}")

@dp.message(Command('delete'))
async def delete_birthday_handler(message: types.Message):
    text = message.text
    if not text:
        await message.answer("❌ Укажите имя: /delete <Имя>")
        return

    name = text.strip()[8:].strip()  # Убираем "/delete " и лишние пробелы
    if not name:
        await message.answer("❌ Укажите имя: /delete <Имя>")
        return

    if delete_birthday(message.from_user.id, name):
        await message.answer(f"✅ Удалено: {name}")
    else:
        await message.answer(f"❌ Не найдено: {name}")

@dp.message(Command('list'))
async def list_birthdays_handler(message: types.Message):
    birthdays = get_user_birthdays(message.from_user.id)
    if not birthdays:
        await message.answer("📭 У вас пока нет сохранённых дней рождения.")
        return

    text = "📅 Ваши дни рождения:\n"
    for name, date_str in birthdays.items():
        text += f" • {name}: {date_str}\n"
    await message.answer(text)

async def check_birthdays():
    """Проверяет дни рождения и отправляет напоминания за 3 дня."""
    from datetime import datetime, timedelta
    import json
    import os

    # Загружаем все данные
    if not os.path.exists("birthdays.json"):
        return

    try:
        with open("birthdays.json", 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        print("Ошибка чтения birthdays.json")
        return

    # Сегодняшняя дата
    today = datetime.today().date()
    target_date = today + timedelta(days=3)  # Дата через 3 дня
    target_str = target_date.strftime("%m-%d")  # Только месяц и день, например: "05-15"

    for user_id_str, birthdays in all_data.items():
        reminders = []
        for name, full_date_str in birthdays.items():
            # Извлекаем только месяц и день из даты рождения
            try:
                birth_date = datetime.strptime(full_date_str, "%Y-%m-%d").date()
                birth_mm_dd = birth_date.strftime("%m-%d")
                if birth_mm_dd == target_str:
                    reminders.append(name)
            except ValueError:
                continue  # Пропускаем некорректные даты

        if reminders:
            try:
                user_id = int(user_id_str)
                message_text = "🎂 Напоминание!\nЧерез 3 дня день рождения у:\n" + "\n".join(f" • {name}" for name in reminders)
                await bot.send_message(chat_id=user_id, text=message_text)
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

# --- Запуск бота ---
if __name__ == '__main__':
    print("Бот запущен...")

    # Создаём планировщик
    scheduler = AsyncIOScheduler()

    scheduler.add_job(check_birthdays, CronTrigger(hour=9, minute=0))

    # Запускаем бота и планировщик в одном событийном цикле
    async def run_bot():
        try:
            scheduler.start()  # Запускаем планировщик
            await dp.start_polling(bot, skip_updates=True)
        finally:
            scheduler.shutdown()  # Останавливаем при завершении

    asyncio.run(run_bot())