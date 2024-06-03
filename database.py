import sqlite3 as sq

async def database_start():

    global database, cursor

    database = sq.connect("profiles.db")
    cursor = database.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS users("
                   "user_id TEXT PRIMARY KEY, "
                   "fullname TEXT, "
                   "gender TEXT, "
                   "age TEXT, "
                   "height TEXT, "
                   "weight TEXT, "
                   "paid_status TEXT)")

    cursor.execute("CREATE TABLE IF NOT EXISTS Lectory("
                   "lectory_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                   "month TEXT, "
                   "training TEXT)")

    database.commit()

async def create_user(user_id):

    user = cursor.execute("SELECT 1 FROM users WHERE user_id == '{key}' ".format(key=user_id)).fetchone()

    if not user:
        cursor.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?)", (user_id, '', '', '', '', '', 'No'))
        database.commit()

async def create_training(month, training):
    cursor.execute("INSERT INTO Lectory(month, training) VALUES(?, ?)", (month, training))
    database.commit()

async def edit_user(state, user_id):

    async with state.proxy() as data:

        cursor.execute("UPDATE users "
                       "SET fullname = '{}', "
                       "gender = '{}', "
                       "age = '{}', "
                       "height = '{}', "
                       "weight = '{}' WHERE user_id = '{}'".format(
            data['fullname'], data['gender'], data['age'], data['height'], data['weight'], user_id))
        database.commit()

async def get_trainings(month):
    cursor.execute("SELECT training FROM Lectory WHERE month == ?", (month,))
    result = cursor.fetchall()
    text_values = []
    for row in result:
        text_values.append(row)
    return text_values


async def pay(user_id):

    cursor.execute("UPDATE users SET paid_status = 'Yes' WHERE user_id = '{key}'".format(key=user_id)).fetchone()
    database.commit()
