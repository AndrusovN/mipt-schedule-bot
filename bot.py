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
today_schedule = {}
users = {}
admin_chat_id = 228041096
users_filename = "users.json"
users_lock = threading.Lock()
logs_lock = threading.Lock()
group_name_pattern = re.compile("Б[0-9][0-9]-[0-9][0-9][0-9]$")


def log(data):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs_lock.acquire()
    with open('logs.txt', 'a') as f:
        f.write(timestamp + " " + str(data) + '\n')
    logs_lock.release()


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
            log("Trouble with reading users")
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
Я бот с расписанием МФТИ. Расписание работает для всех групп как бакалавриата, так и магистратуры!
Напиши /setgroup <твоя группа> без кавычек, чтобы тебе приходила актуальная информация о приближающихся парах
Можешь написать /info, чтобы узнать, в какой группе ты зарегистрирован в боте
Чтобы посмотреть расписание на сегодня, напиши /rasp
Чтобы отписаться от уведомлений, напиши /unsubscribe''')


@bot.message_handler(commands=['notify_all'])
def notify_all(m):
    if m.chat.id != admin_chat_id:
        try:
            bot.send_message(m.chat.id, "Только админ может выполнить эту команду!")
        except Exception as e:
            log(f"Cannot send message to user {m.chat.id} because of {str(e)}")
        return
    users_lock.acquire()
    message = m.text[12:]
    for user in users.keys():
        try:
            bot.send_message(user, message)
        except Exception as e:
            log(f"Cannot send message to user {user} because of {(str(e))}")
    users_lock.release()


@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(m):
    users_lock.acquire()
    if m.chat.id in users.keys():
        users.pop(m.chat.id)
    bot.send_message(m.chat.id, 'Теперь вы не будете получать уведомления(')
    users_lock.release()


def prepare_beautiful_schedule(schedule):
    pairs = []
    for lesson in schedule:
        lesson_time = lesson[0].split(":")
        lesson_time = int(lesson_time[0])*60 + int(lesson_time[1])
        pairs.append((lesson_time, lesson[0] + " - " + lesson[1]))
    pairs = sorted(pairs, key=lambda x: x[0])
    pairs = [lesson[1] for lesson in pairs]
    return '\n\n'.join(pairs)


@bot.message_handler(commands=['rasp'])
def get_schedule(m):
    users_lock.acquire()
    if m.chat.id not in users.keys():
        try:
            bot.send_message(m.chat.id, "Сначала задайте группу с помощью команды /setgroup <ваша группа>")
        except Exception as e:
            log(f"Unable to send message to user {m.chat.id} because of {str(e)}")
        users_lock.release()
        return
    try:
        group_name = users[m.chat.id]
        if group_name not in today_schedule.keys():
            bot.send_message(m.chat.id, f"Не удалось найти вашу группу {group_name}")
            users_lock.release()
            return
        group_schedule = today_schedule[group_name]
        today = datetime.date.today().weekday()
        today = days[today]
        schedule_text = prepare_beautiful_schedule(group_schedule[today])
        bot.send_message(m.chat.id, schedule_text)
    except Exception as e:
        log(f"Trouble with sending message to {m.chat.id}: {str(e)}")
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
    try:
        if len(parts) != 2:
            bot.send_message(m.chat.id, f'Пожалуйста, после команды введите название группы в том же сообщении')
            return
        if not re.match(group_name_pattern, parts[1]):
            bot.send_message(m.chat.id, f'Название группы должно быть вида БXY-PQR')
            return
        log("going to save")
        users_lock.acquire()
        if m.chat.id not in users.keys():
            log(f"New user joined!!!\nusername: {m.from_user.username}, id: {m.from_user.id}")

        users[m.chat.id] = parts[1]

        users_lock.release()
        save_users()
        log("saved")
        bot.send_message(m.chat.id, f'Вы задали группу: {parts[1]}')
    except Exception as e:
        log(f"Trouble in setting group for {m.chat.id} group {parts} exception {str(e)}")


@bot.message_handler(content_types=['text'])
def easter_egg(m):
    try:
        if m.text == 'РТ':
            bot.send_message(m.chat.id, 'РТ!!!\n\n'*20)
        else:
            bot.send_message(m.chat.id, '''Прости, я пока не умею отвечать на такой запрос(
Если ты считаешь, что в работе бота что-то не так, то напиши команду /report <описание проблемы> без кавычек''')
    except Exception as e:
        log(f"Unable to send message to user {m.chat.id} because of {str(e)}")


def notify(group_name, timestamp, lesson):
    users_lock.acquire()
    for user in users.keys():
        if users[user] == group_name:
            try:
                bot.send_message(user, f"В {timestamp} начинается занятие:\n\n{lesson}")
            except Exception as e:
                log(f"Unable to send message to user {user} because of {str(e)}")
    users_lock.release()


def everyday_update():
    users_lock.acquire()
    log("updating")
    global today_schedule
    today_schedule = update_schedules()
    log("schedule received")
    today = datetime.date.today().weekday()
    today = days[today]
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
    log(f"finished updating - next update in {delay // 60} minutes")


upload_users()
log(users)
bot_thread = threading.Thread(target=bot.polling, kwargs={'none_stop': True, 'interval': 0})
bot_thread.start()
everyday_update()
log("Success")
print("bot is started")
while True:
    time.sleep(1)
