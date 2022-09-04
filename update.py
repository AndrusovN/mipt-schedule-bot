import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.request
import os
import xlrd

url = 'https://mipt.ru/about/departments/uchebniy/schedule/study/'
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
filename = "schedule.xls"


def remake_hours(hours):
    if type(hours) == str:
        hours = hours.split(' - ')[0]
        hours = hours[:-2] + ":" + hours[-2:]
    return hours


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
        if type(item[1]) == str and len(item[1]) > 0:
            current.append(item)
    schedule[days[id]] = current
    return schedule


def receive_excel_file():
    data = requests.get(url)
    bs = BeautifulSoup(data.text)
    result = bs.find(lambda tag: tag.name == "li" and "1 курс бакалавриата, специалитета" in tag.text)
    ref = result.find("a")['href']

    if os.path.exists(filename):
        os.remove(filename)
    else:
        print("The file does not exist")

    urllib.request.urlretrieve("https://mipt.ru" + ref, filename)


def read_excel_file():
    ExcelFile = pd.read_excel(filename)
    xl = xlrd.open_workbook(filename, formatting_info=True)
    FirstSheet = xl.sheet_by_index(0)
    for crange in FirstSheet.merged_cells:
        # print("there")
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
    df = pd.read_excel(io="schedule.xls", sheet_name="1 курс")
    df.columns = df.iloc[3]
    hours = df['Часы'].iloc[:, 0].tolist()
    hours = hours[4:]

    return [remake_hours(x) for x in hours]


def update_schedules():
    receive_excel_file()

    df = read_excel_file()

    group_names = list(filter(lambda x: type(x) == str and x[0] == 'Б', df.columns.tolist()))
    lessons = {group_name: df[group_name].tolist()[4:] for group_name in group_names}

    hours = parse_lesson_hours()

    schedules = {group_name: make_schedule(group_name, hours, lessons) for group_name in group_names}
    return schedules
