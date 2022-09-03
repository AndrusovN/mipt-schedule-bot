import telebot
import threading
import time
from update import update_schedules, days
import datetime
import json
import os
import re


# Создаем экземпляр бота
bot = telebot.TeleBot(input('Введите токен бота:\n'))
users = {}
admin_chat_id = 228041096
users_filename = "users.json"
users_lock = threading.Lock()
group_name_pattern = re.compile("Б[0-9][0-9]-[0-9][0-9][0-9]$")


def upload_users():
    global users
    users_lock.acquire()
    if not os.path.exists(users_filename):
        users = {}
        users_lock.release()
        return
    with open(users_filename, 'r') as f:
        data = f.read()
        try:
            users_str = json.loads(data)
            users = {int(key): value for key, value in users_str.items()}
        except:
            print("Trouble with reading users")
            users = {}
    users_lock.release()


def save_users():
    users_lock.acquire()
    with open(users_filename, 'w') as f:
        f.write(json.dumps(users))
    users_lock.release()


@bot.message_handler(commands=['report'])
def report(m):
    bot.send_message(admin_chat_id, "Bug report from user:\n" + m.from_user.username + "\n" + m.text[8:])


# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id, f'''Привет, {m.from_user.first_name}! 
Я бот с расписанием МФТИ. Пока расписание работает только для первого курса
Напиши /setgroup <твоя группа> без кавычек, чтобы тебе приходила актуальная информация о приближающихся парах
Можешь написать /info, чтобы узнать, в какой группе ты зарегистрирован в боте
Чтобы отписаться от уведомлений, напиши /unsubscribe''')


@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(m):
    users_lock.acquire()
    if m.chat.id in users.keys():
        users.pop(m.chat.id)
    bot.send_message(m.chat.id, 'Теперь вы не будете получать уведомления(')
    users_lock.release()


@bot.message_handler(commands=['info'])
def info(m):
    users_lock.acquire()
    if m.chat.id in users.keys():
        bot.send_message(m.chat.id, f'Вы отслеживаете группу {users[m.chat.id]}')
    else:
        bot.send_message(m.chat.id, '''Пока вы не отслеживаете никакую группу(
Напишите /setgroup <ваша группа> без кавычек, чтобы получать уведомления о приближающихся парах''')
    users_lock.release()


@bot.message_handler(commands=["setgroup"])
def set_group(m):
    parts = m.text.split(' ')
    if len(parts) != 2:
        bot.send_message(m.chat.id, f'Пожалуйста, после команды введите название группы в том же сообщении')
        return
    if not re.match(group_name_pattern, parts[1]):
        bot.send_message(m.chat.id, f'Название группы должно быть вида БXY-PQR')
        return
    print("going to save")
    users_lock.acquire()
    if m.chat.id not in users.keys():
        print(f"New user joined!!!\nusername: {m.from_user.username}, id: {m.from_user.id}")

    users[m.chat.id] = parts[1]

    users_lock.release()
    save_users()
    print("saved")
    bot.send_message(m.chat.id, f'Вы задали группу: {parts[1]}')


@bot.message_handler(content_types=['text'])
def easter_egg(m):
    if m.text == 'РТ':
        bot.send_message(m.chat.id, 'РТ!!!\n\n'*20)
    else:
        bot.send_message(m.chat.id, '''Прости, я пока не умею отвечать на такой запрос(
Если ты считаешь, что в работе бота что-то не так, то напиши команду /report <описание проблемы> без кавычек''')


def notify(group_name, timestamp, lesson):
    users_lock.acquire()
    for user in users.keys():
        if users[user] == group_name:
            bot.send_message(user, f"В {timestamp} начинается занятие:\n\n{lesson}")
    users_lock.release()


def everyday_update():
    users_lock.acquire()
    print("updating")
    today_schedule = update_schedules()
    print("schedule received")
    today = datetime.date.today().weekday()
    today = days[today - 5]
    now = datetime.datetime.now()
    today_str = str(datetime.date.today())[:10] + ' '
    for i, group in enumerate(today_schedule.keys()):
        current = today_schedule[group][today]
        for lesson in current:
            daytime = today_str + lesson[0] + ":00"
            runtime = datetime.datetime.strptime(daytime, "%Y-%m-%d %H:%M:%S")
            delay = (runtime - now).total_seconds() - 15*60 - i
            if delay > 0:
                threading.Timer(delay, notify, (group, lesson[0], lesson[1])).start()
    next_update = str(datetime.date.today() + datetime.timedelta(days=1))[:10] + " 08:30:00"
    next_update = datetime.datetime.strptime(next_update, "%Y-%m-%d %H:%M:%S")
    delay = (next_update - datetime.datetime.now()).total_seconds()
    threading.Timer(delay, everyday_update).start()
    users_lock.release()
    print(f"finished updating - next update in {delay // 60} minutes")


upload_users()
print(users)
bot_thread = threading.Thread(target=bot.polling, kwargs={'none_stop': True, 'interval': 0})
bot_thread.start()
everyday_update()
print("Success")
while True:
    time.sleep(1)
