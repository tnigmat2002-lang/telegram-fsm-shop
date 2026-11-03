import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "your token"
ADMIN_ID = your id

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Настройка базы данных
def db_start():
    conn = sqlite3.connect('orders.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        item TEXT,
        phone TEXT
    )''')
    conn.commit()
    conn.close()

class OrderState(StatesGroup):
    waiting_for_item = State()
    waiting_for_phone = State()

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Сделать заказ")], 
        [KeyboardButton(text="📞 Контакты")]
    ],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Добро пожаловать в магазин! Выберите действие:", reply_markup=main_kb)

@dp.message(F.text == "📞 Контакты")
async def contacts_cmd(message: Message):
    await message.answer("Наш телефон: +7 (999) 000-00-00\nАдрес: Интернет")

@dp.message(F.text == "🛒 Сделать заказ")
async def start_order(message: Message, state: FSMContext):
    await message.answer("Что вы хотите заказать? Напишите название товара.")
    await state.set_state(OrderState.waiting_for_item)

@dp.message(OrderState.waiting_for_item)
async def process_item(message: Message, state: FSMContext):
    await state.update_data(item=message.text)
    await message.answer("Отлично. Теперь укажите ваш номер телефона:")
    await state.set_state(OrderState.waiting_for_phone)

@dp.message(OrderState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    item = data['item']
    phone = message.text
    username = message.from_user.username or "Без_юзернейма"
    
    # Сохраняем в базу данных
    conn = sqlite3.connect('orders.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO orders (username, item, phone) VALUES (?, ?, ?)", (username, item, phone))
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ Заказ оформлен!\nТовар: {item}\nТелефон: {phone}\nМенеджер свяжется с вами.")
    await bot.send_message(ADMIN_ID, f"🚨 НОВЫЙ ЗАКАЗ!\nПокупатель: @{username}\nТовар: {item}\nТелефон: {phone}")
    await state.clear()

# Скрытая админка (сработает только для твоего ID)
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect('orders.db')
        cur = conn.cursor()
        orders = cur.execute("SELECT * FROM orders").fetchall()
        conn.close()
        
        if not orders:
            await message.answer("Заказов пока нет.")
            return
            
        res = "<b>Список заказов:</b>\n\n"
        for o in orders:
            res += f"ID: {o[0]} | @{o[1]} | {o[2]} | {o[3]}\n"
        await message.answer(res, parse_mode="HTML")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

async def main():
    db_start() # Создаем файл БД при запуске
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
