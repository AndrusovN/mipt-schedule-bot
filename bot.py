import telebot
import threading
import time
from update import update_schedules, days
import datetime
import json


# Создаем экземпляр бота
bot = telebot.TeleBot(input('Введите токен бота:\n'))
users = {}
admin_chat_id = 228041096
users_filename = "users.json"


def upload_users():
    global users
    with open(users_filename, 'r') as f:
        data = f.read()
        try:
            users = json.loads(data)
        except:
            print("Trouble with reading users")
            users = {}


def save_users():
    with open(users_filename, 'w') as f:
        f.write(json.dumps(users))


@bot.message_handler(commands=['report'])
def report(m):
    bot.send_message(admin_chat_id, "Bug report from user:\n" + m.from_user.username + "\n" + m.text[8:])


# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id, f'''Привет, {m.from_user.first_name}! 
Я бот с расписанием МФТИ. Пока расписание работает только для первого курса
Напиши /setgroup <твоя группа> без кавычек, чтобы тебе приходила актуальная информация о приближающихся парах''')


@bot.message_handler(commands=["setgroup"])
def set_group(m):
    parts = m.text.split(' ')
    if len(parts) != 2:
        bot.send_message(m.chat.id, f'Пожалуйста, после команды введите название группы в том же сообщении')
        return
    if parts[1][0] != "Б":
        bot.send_message(m.chat.id, f'Пожалуйста, введите корректное название группы')
        return
    if m.chat.id not in users.keys():
        print(f"New user joined!!!\nusername: {m.from_user.username}, id: {m.from_user.id}")

    users[m.chat.id] = parts[1]
    save_users()
    bot.send_message(m.chat.id, f'Вы задали группу: {parts[1]}')


@bot.message_handler(content_types=['text'])
def easter_egg(m):
    if m.text == 'РТ':
        bot.send_message(m.chat.id, 'РТ!!!\n\n'*20)
    else:
        bot.send_message(m.chat.id, '''Прости, я пока не умею отвечать на такой запрос(
Если ты считаешь, что в работе бота что-то не так, то напиши команду /report <описание проблемы> без кавычек''')


def notify(group_name, timestamp, lesson):
    for user in users.keys():
        if users[user] == group_name:
            bot.send_message(user, f"В {timestamp} начинается занятие:\n\n{lesson}")


def everyday_update():
    print("updating")
    today_schedule = update_schedules()
    print("schedule received")
    today = datetime.date.today().weekday()
    today = days[today - 5]
    now = datetime.datetime.now()
    today_str = str(datetime.date.today())[:10] + ' '
    for group in today_schedule.keys():
        current = today_schedule[group][today]
        for lesson in current:
            daytime = today_str + lesson[0] + ":00"
            runtime = datetime.datetime.strptime(daytime, "%Y-%m-%d %H:%M:%S")
            delay = (runtime - now).total_seconds() - 15*60
            if delay > 0:
                threading.Timer(delay, notify, (group, lesson[0], lesson[1])).start()
    next_update = str(datetime.date.today() + datetime.timedelta(days=1))[:10] + " 08:30:00"
    next_update = datetime.datetime.strptime(next_update, "%Y-%m-%d %H:%M:%S")
    delay = (next_update - datetime.datetime.now()).total_seconds()
    threading.Timer(delay, everyday_update).start()
    print(f"finished updating - next update in {delay // 60} minutes")


upload_users()
bot_thread = threading.Thread(target=bot.polling, kwargs={'none_stop': True, 'interval': 0})
bot_thread.start()
everyday_update()
print("Success")
while True:
    time.sleep(1)
