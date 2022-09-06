import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.request
import os
import xlrd

url = 'https://mipt.ru/about/departments/uchebniy/schedule/study/'
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
filename = "schedule.xls"
sheetnames = ['1 курс бакалавриата, специалитета', '2 курс бакалавриата, специалитета',
              '3 курс бакалавриата, специалитета', '4 курс бакалавриата, специалитета',
              '1 курс магистратуры, 5 курс специалитета', '2 курс магистратура, 6 курс ФАКИ',
              '2 курс магистратура, 6 курс ФПМИ']


def remake_hours(hours):
    if type(hours) == str:
        hours = hours.split(' - ')[0]
        hours = hours[:-2] + ":" + hours[-2:]
    return hours


def verify_lesson(lesson):
    return type(lesson) == str and len(lesson) > 0 and \
           "в г. Москве" not in lesson and 'в г. Долгопрудном' not in lesson \
           and 'Базовый день' not in lesson


def make_schedule(group_name, hours, lessons):
    pairs = []
    for i in range(min(len(hours), len(lessons[group_name]))):
        if type(hours[i]) == str:
            pairs.append((hours[i], lessons[group_name][i]))

    schedule = {}
    current = []
    id = 0
    for item in pairs:
        if item[0] == '9:00' and len(current) != 0:
            schedule[days[id]] = current
            current = []
            id += 1
        if verify_lesson(item[1]):
            current.append(item)
    schedule[days[id]] = current
    return schedule


def receive_excel_file(sheet_name):
    data = requests.get(url)
    bs = BeautifulSoup(data.text)
    result = bs.find(lambda tag: tag.name == "li" and sheet_name in tag.text)
    ref = result.find("a")['href']

    if os.path.exists(filename):
        os.remove(filename)

    urllib.request.urlretrieve("https://mipt.ru" + ref, filename)


def read_excel_file():
    ExcelFile = pd.read_excel(filename)
    xl = xlrd.open_workbook(filename, formatting_info=True)
    FirstSheet = xl.sheet_by_index(0)
    for crange in FirstSheet.merged_cells:
        rlo, rhi, clo, chi = crange
        for rowx in range(rlo, rhi):
            for colx in range(clo, chi):
                value = FirstSheet.cell(rowx, colx).value
                if len(value) == 0:
                    try:
                        ExcelFile.iloc[rowx - 1, colx - 1] = FirstSheet.cell(rlo, clo).value
                    except:
                        pass

    df = ExcelFile
    df.columns = df.iloc[3]
    return df


def parse_lesson_hours():
    df = pd.read_excel(io="schedule.xls", sheet_name='6 курс')
    df.columns = df.iloc[3]
    hours = df['Часы'].iloc[:, 0].tolist()
    hours = hours[4:]

    return [remake_hours(x) for x in hours]


def update_schedules():
    group_names = []
    lessons = {}
    for sheet in sheetnames:
        receive_excel_file(sheet)

        df = read_excel_file()

        titles = df.columns.tolist()
        current_group_names = list(filter(lambda x: type(x) == str and (x[0] == 'Б' or x[0] == 'М' or x[0] == 'С')
                                                    and titles.count(x) == 1, df.columns.tolist()))
        print(current_group_names)
        print(len(current_group_names))
        print(len(set(current_group_names)))
        current_lessons = {group_name: df[group_name].tolist()[4:] for group_name in current_group_names}
        group_names = group_names + current_group_names
        lessons = {**lessons, **current_lessons}

    hours = parse_lesson_hours()

    schedules = {group_name: make_schedule(group_name, hours, lessons) for group_name in group_names}
    return schedules
