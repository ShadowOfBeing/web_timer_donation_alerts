from datetime import timedelta
import requests
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request
from donationalerts import Alert
from datetime import datetime
from utils import *


plus_time = 0
donations_ids = []
donations_ids = []
alert = Alert(token)
app = Flask(__name__)


def get_exchange_rate(currency):
    url = f'http://www.cbr.ru/scripts/XML_daily.asp?date_req={datetime.now().strftime("%d/%m/%Y")}'
    response = requests.get(url)

    # Разбор XML
    root = ET.fromstring(response.content)

    # Преобразование в словарь
    currency_dict = {}
    for valute in root.findall('Valute'):
        char_code = valute.find('CharCode').text
        if char_code in ['USD', 'EUR']:
            valute_data = {
                'NumCode': valute.find('NumCode').text,
                'Nominal': valute.find('Nominal').text,
                'Name': valute.find('Name').text,
                'Value': valute.find('Value').text,
                'VunitRate': valute.find('VunitRate').text
            }
            currency_dict[char_code] = valute_data
    rate = float(currency_dict[currency]['Value'].replace(',', '.'))

    return rate


def write_donations_to_file(donate_id, flag='ok'):
    current_datetime = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    with open(f"{file_name}.txt", 'a', encoding='windows-1251') as file:
        if flag == 'ok':
            file.write(f"{current_datetime} id({donate_id}) сумма({plus_time // seconds_for_ruble}) прибавил_времени({seconds_to_time(plus_time)})\n")
        elif flag == 'error':
            file.write(f"{current_datetime} id({donate_id}) сумма({plus_time}) ошибка_конвертации\n")


def seconds_to_time(seconds):
    time_obj = datetime(1, 1, 1) + timedelta(seconds=seconds)
    return time_obj.time()


def subtract_one_second(time_str):
    # Преобразуем строку времени в объект datetime
    time_obj = datetime.strptime(time_str, '%H:%M:%S')

    # Вычитаем одну секунду
    new_time_obj = time_obj - timedelta(seconds=1)

    # Преобразуем обратно в строку в формате "HH:MM:SS"
    new_time_str = new_time_obj.strftime('%H:%M:%S')

    return new_time_str


def plus_donate_time(start_time, different):
    # Преобразуем строку времени в объект datetime
    time_obj = datetime.strptime(start_time, '%H:%M:%S')

    # Плюсуем донатное время
    new_time_obj = time_obj + timedelta(seconds=different)

    # Преобразуем обратно в строку в формате "HH:MM:SS"
    new_time_str = new_time_obj.strftime('%H:%M:%S')

    return new_time_str


@alert.event()
def new_donation(event):
    global plus_time
    """
    event.username - имя пользователя
    event.objects - JSON объект
    """
    data = event.objects
    amount = data['amount_main']

    if data['currency'] != 'RUB':
        if data['amount_main'] == data['amount']:
            if data['currency'] in ['USD', 'EUR']:
                rate = get_exchange_rate(data['currency'])
                amount = float(data['amount']) * rate
                print(rate, amount)
            else:
                amount = 0

    if not (data['id'] in donations_ids):
        plus_time += int(amount * seconds_for_ruble)
        donations_ids.append(data['id'])
        if amount == 0:
            write_donations_to_file(data['id'], 'error')
        print(f"Прибавилось секунд: {plus_time}")
        print()
    return 0


@app.route('/')
def index():
    global plus_time

    obs_timer_string = request.args.get('source')

    if obs_timer_string == "end_time":
        return end_phrase
    else:
        current_timer = subtract_one_second(obs_timer_string)
        if plus_time:
            current_timer = plus_donate_time(current_timer, plus_time)
            write_donations_to_file(donations_ids[-1])
            plus_time = 0
        if current_timer == "00:00:00":
            current_timer = end_phrase

    return current_timer


@app.route('/main')
def main_page():
    return render_template('main.html')


if __name__ == "__main__":
    app.run(debug=True)
