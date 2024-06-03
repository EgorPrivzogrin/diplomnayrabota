from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from database import database_start, create_user, edit_user, pay
import spk

import sqlite3
import config

async def on_startup(_):
    await database_start()

storage = MemoryStorage()
bot = Bot(config.admin_token)
dp = Dispatcher(bot, storage=storage)

conn = sqlite3.connect('profiles.db')
cursor = conn.cursor()

class TrainingStates(StatesGroup):
    waiting_for_month = State()
    waiting_for_training = State()

month_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
month_keyboard.add('Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь')

material_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
material_keyboard.add('Добавить лекционный материал')

@dp.message_handler(commands=['start'])
async def start_conversation(message: types.Message):
    await message.answer('Выберите что вы хотите изменить:', reply_markup= material_keyboard)

@dp.message_handler(text='Добавить лекционный материал')
async def get_month(message: types.Message):
    await TrainingStates.waiting_for_month.set()
    await message.answer('Выберите месяц', reply_markup=month_keyboard)

@dp.message_handler(state=TrainingStates.waiting_for_month)
async def handle_month(message: types.Message, state: FSMContext):
    month = message.text
    await state.update_data(month=month)
    await TrainingStates.next()
    await message.answer('Введите текст лекционного материала:', reply_markup=material_keyboard)

@dp.message_handler(state=TrainingStates.waiting_for_training)
async def handle_training(message: types.Message, state: FSMContext):
    training_text = message.text
    data = await state.get_data()
    month = data['month']
    cursor.execute("INSERT INTO Lectory (month, training) VALUES (?, ?)", (month, training_text))
    conn.commit()
    await message.answer('Информация успешно добавлена в БД!')
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
