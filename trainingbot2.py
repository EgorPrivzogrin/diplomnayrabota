from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove  #Remove удаление клавы
import sqlite3
import config
from database import get_trainings, database_start, create_user, edit_user, pay
import spk
conn = sqlite3.connect('profiles.db')
cursor = conn.cursor()

async def on_startup(_):
    await database_start()

storage = MemoryStorage()
bot = Bot(config.token)
price = types.LabeledPrice(label="Подписка на бота", amount=199*100)
dp = Dispatcher(bot, storage=storage)

#Кнопочки клавиатуры
def kb_1() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('🙌🏻Приступим!'))

    return kb

def kb_2() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Мужской'))
    kb.add(KeyboardButton('Женский'))

    return kb

def kb_3() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('📝Показать анкету и изменить анкету📝'))
    kb.add(KeyboardButton('Расчёт индекса массы тела'))
    kb.add(KeyboardButton('Информация о тренере'))
    kb.add(KeyboardButton('Расчёт суточной потребности калорий'))
    kb.add(KeyboardButton('Оплатить подписку'))
    kb.add(KeyboardButton('📚Лекционный материал по тренировкам и питанию📚'))
    

    return kb

def kb_4() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('🔴Сидячий образ жизни'))
    kb.add(KeyboardButton('🟠Небольшая активность'))
    kb.add(KeyboardButton('🟡Умеренная активность'))
    kb.add(KeyboardButton('🟢Высокая активность'))
    kb.add(KeyboardButton('🗿Очень высокая активность'))
    kb.add(KeyboardButton('🔙Назад'))

    return kb

#Инлайновые кнопочки
catalog_list = InlineKeyboardMarkup(row_width=2)
catalog_list.add(InlineKeyboardButton(text='⏲Изменить вес', callback_data='edit_weight'),
                 InlineKeyboardButton(text='📏Изменить рост', callback_data='edit_height'),
                 InlineKeyboardButton(text='📆Изменить возраст', callback_data='edit_age'),
                 InlineKeyboardButton(text='⚤Изменить пол', callback_data='edit_gender'),
                 InlineKeyboardButton(text='Изменить ФИО', callback_data='edit_fullname'),
                 InlineKeyboardButton(text='Удалить анкету', callback_data='delete_form'))

month_list = InlineKeyboardMarkup(row_width=2)
month_list.add(InlineKeyboardButton(text="Январь", callback_data="Январь"),
            InlineKeyboardButton(text="Февраль", callback_data="Февраль"),
            InlineKeyboardButton(text="Март", callback_data="Март"),
            InlineKeyboardButton(text="Апрель", callback_data="Апрель"),
            InlineKeyboardButton(text="Май", callback_data="Май"),
            InlineKeyboardButton(text="Июнь", callback_data="Июнь"),
            InlineKeyboardButton(text="Июль", callback_data="Июль"),
            InlineKeyboardButton(text="Август", callback_data="Август"),
            InlineKeyboardButton(text="Сентябрь", callback_data="Сентябрь"),
            InlineKeyboardButton(text="Октябрь", callback_data="Октябрь"),
            InlineKeyboardButton(text="Ноябрь", callback_data="Ноябрь"),
            InlineKeyboardButton(text="Декабрь", callback_data="Декабрь"))

class ClientStates(StatesGroup):
    fullname = State()
    gender = State()
    weight = State()
    height = State()
    age = State()
    edit_profile = State()
    edit_fullname = State()
    edit_gender = State()
    edit_weight = State()
    edit_height = State()
    edit_age = State()
    select_month = State()
    delete_form = State()



@dp.message_handler(lambda message: message.text == '📚Лекционный материал по тренировкам и питанию📚')
async def show_trainings(message: types.Message):
    cursor.execute("SELECT paid_status FROM users WHERE user_id == '{key}' ".format(key=message.from_user.id))
    data = cursor.fetchall()
    for row in data:
        st = str(row[0])
        if st == 'Yes':
            await ClientStates.select_month.set()
            await message.answer(text="Выберите месяц:", parse_mode='html', reply_markup= month_list)
        else:
            await message.answer(text="Чтобы получить доступ оплатите подписку", parse_mode='html', reply_markup=kb_3())

@dp.callback_query_handler(lambda c: c.data in ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"], state=ClientStates.select_month)
async def send_trainings(callback_query: types.CallbackQuery, state: FSMContext):
    month = callback_query.data
    trainigs_by_month = await get_trainings(month)
    await bot.send_message(callback_query.from_user.id, trainigs_by_month)
    await state.finish()

#Стартовая строка
@dp.message_handler(commands=['start'])
async def start_text(message: types.Message) -> None:
    await message.answer(text="Добро пожаловать, я помогу Вам составить индивидуальную "
                     "программу фитнес-тренировок и питания.", parse_mode='html', reply_markup=kb_1()) #написать сообщение text
    await create_user(user_id=message.from_user.id)
    await message.delete()


#Изменение данных анкеты
@dp.callback_query_handler(lambda c: c.data == "edit_fullname", state=ClientStates.edit_profile)
async def edit_fullname(callback_query: types.CallbackQuery, state: FSMContext):
    await ClientStates.edit_fullname.set()
    await bot.send_message(callback_query.from_user.id, text="Введите новое ФИО:", parse_mode='html')

@dp.message_handler(state=ClientStates.edit_fullname)
async def load_new_fullname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['new_fullname'] = message.text
    if not message.text.isdigit() and any(char in "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюяABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" for char in message.text):
        cursor.execute(f"Update users SET fullname ='{data['new_fullname']}' where user_id={message.from_user.id}")
        conn.commit()
        await message.answer(text="ФИО успешно изменено!", parse_mode='html', reply_markup=kb_3())
        await state.finish()
    else:
        await message.answer(text="Введите реальные ФИО используя только буквы кириллицы или латиницы!", parse_mode='html')

@dp.callback_query_handler(lambda c: c.data == "edit_gender", state=ClientStates.edit_profile)
async def edit_gender(callback_query: types.CallbackQuery, state: FSMContext):
    await ClientStates.edit_gender.set()
    await bot.send_message(callback_query.from_user.id, text="Выберите пол:", parse_mode='html', reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Мужской"), KeyboardButton("Женский")]
        ],
        resize_keyboard=True
    ))

@dp.message_handler(state=ClientStates.edit_gender)
async def load_new_gender(message: types.Message, state: FSMContext):
    if message.text == "Мужской" or message.text == "Женский":
        cursor.execute(f"Update users SET gender ='{message.text}' where user_id={message.from_user.id}")
        conn.commit()
        await message.answer(text="Пол успешно изменен!", parse_mode='html', reply_markup=kb_3())
        await state.finish()
    else:
        await message.answer(text="Выберите пол из предложенных вариантов:", parse_mode='html')

@dp.callback_query_handler(lambda c: c.data == "edit_weight", state=ClientStates.edit_profile)
async def edit_weight(callback_query: types.CallbackQuery, state: FSMContext):
    await ClientStates.edit_weight.set()
    await bot.send_message(callback_query.from_user.id, text="Введите новый вес:", parse_mode='html')

@dp.message_handler(state=ClientStates.edit_weight)
async def load_new_weight(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 20 < int(message.text) < 200:
        cursor.execute(f"Update users SET weight ={message.text} where user_id={message.from_user.id}")
        conn.commit()
        await message.answer(text="Вес успешно изменен!", parse_mode='html', reply_markup=kb_3())
        await state.finish()
    else:
        await message.answer(text="Введите корректный вес!", parse_mode='html')

@dp.callback_query_handler(lambda c: c.data == "edit_height", state=ClientStates.edit_profile)
async def edit_height(callback_query: types.CallbackQuery, state: FSMContext):
    await ClientStates.edit_height.set()
    await bot.send_message(callback_query.from_user.id, text="Введите новый рост:", parse_mode='html')

@dp.message_handler(state=ClientStates.edit_height)
async def load_new_height(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 100 < int(message.text) < 250:
        cursor.execute(f"Update users SET height ={message.text} where user_id={message.from_user.id}")
        conn.commit()
        await message.answer(text="Рост успешно изменен!", parse_mode='html', reply_markup=kb_3())
        await state.finish()
    else:
        await message.answer(text="Введите корректный рост!", parse_mode='html')

@dp.callback_query_handler(lambda c: c.data == "edit_age", state=ClientStates.edit_profile)
async def edit_age(callback_query: types.CallbackQuery, state: FSMContext):
    await ClientStates.edit_age.set()
    await bot.send_message(callback_query.from_user.id, text="Введите новый возраст:", parse_mode='html')

@dp.message_handler(state=ClientStates.edit_age)
async def load_new_age(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 10 < int(message.text) < 100:
        cursor.execute(f"Update users SET age ={message.text} where user_id={message.from_user.id}")
        conn.commit()
        await message.answer(text="Возраст успешно изменен!", parse_mode='html', reply_markup=kb_3())
        await state.finish()
    else:
        await message.answer(text="Введите корректный возраст!", parse_mode='html')

@dp.callback_query_handler(lambda c: c.data == "delete_form", state=ClientStates.edit_profile)
async def edit_gender(callback_query: types.CallbackQuery, state: FSMContext):
    await ClientStates.delete_form.set()
    await bot.send_message(callback_query.from_user.id, text="Вы уверены, что хотите удалить анкету?", parse_mode='html', reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Да"), KeyboardButton("Нет")]
        ],
        resize_keyboard=True
    ))

@dp.message_handler(state=ClientStates.delete_form)
async def load_new_gender(message: types.Message, state: FSMContext):
    if message.text == "Да":
        cursor.execute(f"Update users SET age = NULL, weight = NULL, fullname = NULL, gender = NULL, height = NULL where user_id={message.from_user.id}")
        conn.commit()
        await message.answer(text="Анкета успешно удалена!", parse_mode='html', reply_markup=kb_3())
        await state.finish()
    elif message.text == "Нет":
        await message.answer(text="Вы отменили удаление анкеты!", parse_mode='html', reply_markup=kb_3())
        await state.finish()


#Валидация данных анкеты
@dp.message_handler(lambda message:message.text.isdigit() or not any(char in "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрст"
    "уфхцчшщъыьэюяABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" for char in message.text), state=ClientStates.fullname)
async def check_gender(message: types.Message):
    await message.answer('Введите реальные ФИО используя только буквы кириллицы или латиницы!')

@dp.message_handler(lambda message:  message.text not in("Мужской","Женский"), state=ClientStates.gender)
async def check_gender(message: types.Message):
    await message.answer('Для ввода пола воспользуйтесь кнопками на клавиатуре или напишите ваш пол в формате:Мужской, Женский!')

@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) > 100 or float(message.text) < 10, state=ClientStates.age)
async def check_age(message: types.Message):
    await message.answer('Введите реальный возраст!')

@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) > 250 or float(message.text) < 100, state=ClientStates.height)
async def check_age(message: types.Message):
    await message.answer('Введите реальный рост!')

@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) > 200 or float(message.text) < 20, state=ClientStates.weight)
async def check_age(message: types.Message):
    await message.answer('Введите реальный вес!')






#Выводы кнопок клавиатуры
@dp.message_handler(content_types=['text'])
async def start_work(message: types.Message) -> None:
    if message.text == '🙌🏻Приступим!':
        await ClientStates.fullname.set()
        await message.answer(text="💬Расскажите мне о себе.", parse_mode='html')
        await message.answer(text="Напишите Ваше ФИО:", parse_mode='html', reply_markup=ReplyKeyboardRemove())#написать сообщение text

    elif message.text == '🔙Назад':
        await message.answer(text="Вас вернуло в главное меню", parse_mode='html',reply_markup=kb_3())

    elif message.text == 'Оплатить подписку':
        await message.answer(text="Вы приступили к оплате подписки", parse_mode='html',reply_markup=kb_3())
        await bot.send_invoice(message.chat.id,
                               title="Подписка на бота",
                               description="Активация бессрочной подписки для получения доступа к боту",
                               provider_token=config.pay_token,
                               currency="rub",
                               is_flexible=False,
                               prices=[price],
                               start_parameter="full_access",
                               payload="test-invoice-payload")

    elif message.text == 'Информация о тренере':
        await message.answer(text=str(spk.info_of_coach), parse_mode='html', reply_markup=kb_3())

    elif message.text == "📝Показать анкету и изменить анкету📝":
        cursor.execute("SELECT fullname, gender, age, height, weight FROM users WHERE user_id == '{key}' ".format(key=message.from_user.id))
        data = cursor.fetchall()
        await ClientStates.edit_profile.set()

        for row in data:
            fio = str(row[0])
            pol = str(row[1])
            let = str(row[2])
            rost = str(row[3])
            ves = str(row[4])

        await message.bot.send_message(message.from_user.id, "ФИО: " + fio + "\n" +"⚤Пол: " + pol+"\n"+"📆Возраст: " + let +"\n"+"📏Рост: "
                                       + rost +"\n"+"⏲Вес: " + ves,reply_markup= catalog_list)

    elif message.text == 'Расчёт индекса массы тела':
        await message.answer(text=str(spk.IMT), parse_mode='html', reply_markup=kb_3())

        cursor.execute("SELECT height, weight FROM users WHERE user_id == '{key}' ".format(key=message.from_user.id))
        data = cursor.fetchall()

        for row in data:
            rost = (row[0])
            ves = (row[1])

        if rost and ves!= "":
            await bot.send_message(message.from_user.id,"Ваш индекс массы тела составляет: " + str(round((float(ves)/(float(rost)/100)**2),1)), parse_mode='html', reply_markup=kb_3())
        else:
            await bot.send_message(message.from_user.id,"Недостаточно данных для расчёта ИМТ. Заполните анкету. ", parse_mode='html', reply_markup=kb_3())



    elif message.text == 'Расчёт суточной потребности калорий':
        await message.answer(text="Какой у Вас образ жизни?"+'\n'+str(spk.obraz_zhizny), parse_mode='html', reply_markup=kb_4())

    elif message.text == "🔴Сидячий образ жизни":
        cursor.execute("SELECT gender, age, height, weight FROM users WHERE user_id == '{key}' ".format(key=message.from_user.id))
        data = cursor.fetchall()

        for row in data:
            pol1 = (row[0])
            let1 = (row[1])
            rost1 = (row[2])
            ves1 = (row[3])

            if pol1 and let1 and rost1 and ves1 !="":
                pol = str(pol1)
                let = float(let1)
                rost = float(rost1)
                ves = float(ves1)

                if pol == 'Женский':
                    await bot.send_message(message.from_user.id, "СПК для Вас составаит: " + str(round(((10*ves + 6.25*rost - 4.92*let - 161)*1.2)))+" ккал\n"
                                        "✔Умеренный дефицит = " + str(round(0.85*((10*ves + 6.25*rost - 4.92*let - 161)*1.2))) +
                                        "-" + str(round(0.8*((10*ves + 6.25*rost - 4.92*let - 161)*1.2))) +" ккал\n"
                                        "🟢Cредний дефицит = " + str(round(0.8*((10*ves + 6.25*rost - 4.92*let - 161)*1.2))) +
                                        "-" + str(round(0.75*((10*ves + 6.25*rost - 4.92*let - 161)*1.2))) +" ккал\n"
                                        "🟡Большой дефицит = " + str(round(0.75*((10*ves + 6.25*rost - 4.92*let - 161)*1.2))) +
                                        "-" + str(round(0.7*((10*ves + 6.25*rost - 4.92*let - 161)*1.2))) +" ккал\n"
                                        "🟠Очень большой дефицит (риск) = " + str(round(0.7*((10*ves + 6.25*rost - 4.92*let - 161)*1.2))) +
                                        "-" + str(round(0.6*((10*ves + 6.25*rost - 4.92*let - 161)*1.2))) +" ккал\n"
                                        "🔴Почти голод или голод (опасно) = меньше " + str(round(0.5*((10*ves + 6.25*rost - 4.92*let + 5)*1.2))) +" ккал в день", parse_mode='html', reply_markup=kb_4())
                else:
                    await bot.send_message(message.from_user.id, "СПК для Вас составаит: " + str(round(((10*ves + 6.25*rost - 4.92*let + 5)*1.2)))+" ккал\n"
                                        "✔Умеренный дефицит = " + str(round(0.85*((10*ves + 6.25*rost - 4.92*let + 5)*1.2))) +
                                        "-" + str(round(0.8*((10*ves + 6.25*rost - 4.92*let + 5)*1.2))) +" ккал\n"
                                        "🟢Cредний дефицит = " + str(round(0.8*((10*ves + 6.25*rost - 4.92*let + 5)*1.2))) +
                                        "-" + str(round(0.75*((10*ves + 6.25*rost - 4.92*let + 5)*1.2))) +" ккал\n"
                                        "🟡Большой дефицит = " + str(round(0.75*((10*ves + 6.25*rost - 4.92*let + 5)*1.2))) +
                                        "-" + str(round(0.7*((10*ves + 6.25*rost - 4.92*let + 5)*1.2))) +" ккал\n"
                                        "🟠Очень большой дефицит (риск) = " + str(round(0.7*((10*ves + 6.25*rost - 4.92*let + 5)*1.2))) +
                                        "-" + str(round(0.6*((10*ves + 6.25*rost - 4.92*let + 5)*1.2))) +" ккал\n"
                                        "🔴Почти голод или голод (опасно) = меньше " + str(round(0.5*((10*ves + 6.25*rost - 4.92*let + 5)*1.2))) +" ккал в день", parse_mode='html', reply_markup=kb_4())
            else:
                await bot.send_message(message.from_user.id,"Недостаточно данных для расчёта СПК. Заполните анкету. ", parse_mode='html', reply_markup=kb_3())

    elif message.text == "🟠Небольшая активность":
        cursor.execute("SELECT gender, age, height, weight FROM users WHERE user_id == '{key}' ".format(key=message.from_user.id))
        data = cursor.fetchall()

        for row in data:
            pol1 = (row[0])
            let1 = (row[1])
            rost1 = (row[2])
            ves1 = (row[3])

            if pol1 and let1 and rost1 and ves1 !="":
                pol = str(pol1)
                let = float(let1)
                rost = float(rost1)
                ves = float(ves1)

                if pol == 'Женский':
                    await bot.send_message(message.from_user.id, "СПК для Вас составаит: " + str(round(((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.375))) + " ккал\n"
                                       "✔Умеренный дефицит = " + str(round(0.85 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.375))) +
                                       "-" + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.375))) + " ккал\n"
                                       "🟢Cредний дефицит = " + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.375))) +
                                       "-" + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.375))) + " ккал\n"
                                       "🟡Большой дефицит = " + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.375))) +
                                       "-" + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.375))) + " ккал\n"
                                       "🟠Очень большой дефицит (риск) = " + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.375))) +
                                       "-" + str(round(0.6 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.375))) + " ккал\n"
                                       "🔴Почти голод или голод (опасно) = меньше " + str(round(0.5 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.375))) + " ккал в день",
                                       parse_mode='html', reply_markup=kb_4())
                else:
                    await bot.send_message(message.from_user.id, "СПК для Вас составаит: " + str(round(((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.375))) + " ккал\n"
                                       "✔Умеренный дефицит = " + str(round(0.85 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.375))) +
                                       "-" + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.375))) + " ккал\n"
                                       "🟢Cредний дефицит = " + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.375))) +
                                       "-" + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.375))) + " ккал\n"
                                       "🟡Большой дефицит = " + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.375))) +
                                       "-" + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.375))) + " ккал\n"
                                       "🟠Очень большой дефицит (риск) = " + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.375))) +
                                       "-" + str(round(0.6 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.375))) + " ккал\n"
                                       "🔴Почти голод или голод (опасно) = меньше " + str(round(0.5 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.375))) + " ккал в день",
                                       parse_mode='html', reply_markup=kb_4())
            else:
                await bot.send_message(message.from_user.id,"Недостаточно данных для расчёта СПК. Заполните анкету. ", parse_mode='html', reply_markup=kb_3())

    elif message.text == "🟡Умеренная активность":
        cursor.execute("SELECT gender, age, height, weight FROM users WHERE user_id == '{key}' ".format(key=message.from_user.id))
        data = cursor.fetchall()

        for row in data:
            pol1 = (row[0])
            let1 = (row[1])
            rost1 = (row[2])
            ves1 = (row[3])

            if pol1 and let1 and rost1 and ves1 !="":
                pol = str(pol1)
                let = float(let1)
                rost = float(rost1)
                ves = float(ves1)

                if pol == 'Женский':
                    await bot.send_message(message.from_user.id, "СПК для Вас составаит: " + str(round(((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.55))) + " ккал\n"
                                       "✔Умеренный дефицит = " + str(round(0.85 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.55))) +
                                       "-" + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.55))) + " ккал\n"
                                       "🟢Cредний дефицит = " + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.55))) +
                                       "-" + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.55))) + " ккал\n"
                                       "🟡Большой дефицит = " + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.55))) +
                                       "-" + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.55))) + " ккал\n"
                                       "🟠Очень большой дефицит (риск) = " + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.55))) +
                                       "-" + str(round(0.6 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.55))) + " ккал\n"
                                       "🔴Почти голод или голод (опасно) = меньше " + str(round(0.5 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.55))) + " ккал в день",
                                       parse_mode='html', reply_markup=kb_4())
                else:
                    await bot.send_message(message.from_user.id, "СПК для Вас составаит: " + str(round(((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.55))) + " ккал\n"
                                       "✔Умеренный дефицит = " + str(round(0.85 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.55))) +
                                       "-" + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.55))) + " ккал\n"
                                       "🟢Cредний дефицит = " + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.55))) +
                                       "-" + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.55))) + " ккал\n"
                                       "🟡Большой дефицит = " + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.55))) +
                                       "-" + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.55))) + " ккал\n"
                                       "🟠Очень большой дефицит (риск) = " + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.55))) +
                                       "-" + str(round(0.6 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.55))) + " ккал\n"
                                       "🔴Почти голод или голод (опасно) = меньше " + str(round(0.5 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.55))) + " ккал в день",
                                       parse_mode='html', reply_markup=kb_4())
            else:
                await bot.send_message(message.from_user.id,"Недостаточно данных для расчёта СПК. Заполните анкету. ", parse_mode='html', reply_markup=kb_3())

    elif message.text == "🟢Высокая активность":
        cursor.execute("SELECT gender, age, height, weight FROM users WHERE user_id == '{key}' ".format(key=message.from_user.id))
        data = cursor.fetchall()

        for row in data:
            pol1 = (row[0])
            let1 = (row[1])
            rost1 = (row[2])
            ves1 = (row[3])

            if pol1 and let1 and rost1 and ves1 !="":
                pol = str(pol1)
                let = float(let1)
                rost = float(rost1)
                ves = float(ves1)

                if pol == 'Женский':
                    await bot.send_message(message.from_user.id, "СПК для Вас составаит: " + str(round(((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.725))) + " ккал\n"
                                       "✔Умеренный дефицит = " + str(round(0.85 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.725))) +
                                       "-" + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.725))) + " ккал\n"
                                       "🟢Cредний дефицит = " + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.725))) +
                                       "-" + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.725))) + " ккал\n"
                                       "🟡Большой дефицит = " + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.725))) +
                                       "-" + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.725))) + " ккал\n"
                                       "🟠Очень большой дефицит (риск) = " + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.725))) +
                                       "-" + str(round(0.6 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.725))) + " ккал\n"
                                       "🔴Почти голод или голод (опасно) = меньше " + str(round(0.5 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.725))) + " ккал в день",
                                       parse_mode='html', reply_markup=kb_4())
                else:
                    await bot.send_message(message.from_user.id, "СПК для Вас составаит: " + str(round(((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.725))) + " ккал\n"
                                       "✔Умеренный дефицит = " + str(round(0.85 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.725))) +
                                       "-" + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.725))) + " ккал\n"
                                       "🟢Cредний дефицит = " + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.725))) +
                                       "-" + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.725))) + " ккал\n"
                                       "🟡Большой дефицит = " + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.725))) +
                                       "-" + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.725))) + " ккал\n"
                                       "🟠Очень большой дефицит (риск) = " + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.725))) +
                                       "-" + str(round(0.6 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.725))) + " ккал\n"
                                       "🔴Почти голод или голод (опасно) = меньше " + str(round(0.5 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.725))) + " ккал в день",
                                       parse_mode='html', reply_markup=kb_4())
            else:
                await bot.send_message(message.from_user.id,"Недостаточно данных для расчёта СПК. Заполните анкету. ", parse_mode='html', reply_markup=kb_3())

    elif message.text == "🗿Очень высокая активность":
        cursor.execute("SELECT gender, age, height, weight FROM users WHERE user_id == '{key}' ".format(key=message.from_user.id))
        data = cursor.fetchall()

        for row in data:
            pol1 = (row[0])
            let1 = (row[1])
            rost1 = (row[2])
            ves1 = (row[3])

            if pol1 and let1 and rost1 and ves1 !="":
                pol = str(pol1)
                let = float(let1)
                rost = float(rost1)
                ves = float(ves1)

                if pol == 'Женский':
                    await bot.send_message(message.from_user.id, "СПК для Вас составаит: " + str(round(((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.9))) + " ккал\n"
                                       "✔Умеренный дефицит = " + str(round(0.85 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.9))) +
                                       "-" + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.9))) + " ккал\n"
                                       "🟢Cредний дефицит = " + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.9))) +
                                       "-" + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.9))) + " ккал\n"
                                       "🟡Большой дефицит = " + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.9))) +
                                       "-" + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.9))) + " ккал\n"
                                       "🟠Очень большой дефицит (риск) = " + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.9))) +
                                       "-" + str(round(0.6 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.9))) + " ккал\n"
                                       "🔴Почти голод или голод (опасно) = меньше " + str(round(0.5 * ((10 * ves + 6.25 * rost - 4.92 * let - 161) * 1.9))) + " ккал в день",
                                       parse_mode='html', reply_markup=kb_4())
                else:
                    await bot.send_message(message.from_user.id, "СПК для Вас составаит: " + str(round(((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.9))) + " ккал\n"
                                       "✔Умеренный дефицит = " + str(round(0.85 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.9))) +
                                       "-" + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.9))) + " ккал\n"
                                       "🟢Cредний дефицит = " + str(round(0.8 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.9))) +
                                       "-" + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.9))) + " ккал\n"
                                       "🟡Большой дефицит = " + str(round(0.75 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.9))) +
                                       "-" + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.9))) + " ккал\n"
                                       "🟠Очень большой дефицит (риск) = " + str(round(0.7 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.9))) +
                                       "-" + str(round(0.6 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.9))) + " ккал\n"
                                       "🔴Почти голод или голод (опасно) = меньше " + str(round(0.5 * ((10 * ves + 6.25 * rost - 4.92 * let + 5) * 1.9))) + " ккал в день",
                                       parse_mode='html', reply_markup=kb_4())
            else:
                await bot.send_message(message.from_user.id,"Недостаточно данных для расчёта СПК. Заполните анкету. ", parse_mode='html', reply_markup=kb_3())

@dp.message_handler(state=ClientStates.fullname)
async def load_fullname(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['fullname'] = message.text
    await ClientStates.gender.set()
    await message.answer(text="⚤Укажите Ваш пол:", parse_mode='html', reply_markup=kb_2())

@dp.message_handler(state=ClientStates.gender)
async def load_gender(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['gender'] = message.text
    await ClientStates.age.set()
    await message.answer(text="📆Напишите Ваш возраст:", parse_mode='html', reply_markup=ReplyKeyboardRemove())

@dp.message_handler(state=ClientStates.age)
async def load_age(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['age'] = message.text
    await ClientStates.height.set()
    await message.answer(text="📏Напишите Ваш рост в сантиметрах:", parse_mode='html', reply_markup=ReplyKeyboardRemove())

@dp.message_handler(state=ClientStates.height)
async def load_height(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['height'] = message.text
    await ClientStates.weight.set()
    await message.answer(text="⏲Напишите Ваш вес в кг(округлите до целого значения):", parse_mode='html', reply_markup=ReplyKeyboardRemove())

@dp.message_handler(state=ClientStates.weight)
async def load_weight(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['weight'] = message.text
    await edit_user(state, user_id=message.from_user.id)
    await message.answer(text="📝Анкета создана,\nДля получения доступа ко всему функционалу, Вам необходимо купить подписку",
                         parse_mode='html', reply_markup=kb_3())


    await state.finish()


@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    await pay(user_id=message.from_user.id)
    await bot.send_message(message.chat.id,
                           f"✅Платеж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!",
                           reply_markup=kb_3())



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates = True, on_startup=on_startup)