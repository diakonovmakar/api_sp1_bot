import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

MIN_5 = 5 * 60
SEC_5 = 5

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename='main.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    statuses = {
        'reviewing': f'Ваша работа "{homework_name}" принята. Ждём ревью.',
        'rejected': (
            f'У вас проверили работу "{homework_name}"!'
            ' \n\nК сожалению, в работе нашлись ошибки.'),
        'approved': (
            f'У вас проверили работу "{homework_name}"!'
            '\n\nРевьюеру всё понравилось, работа зачтена!')
    }

    for status, verdict in statuses.items():
        if homework['status'] == status:
            logging.info(f'У работы {homework_name} статус {status}')
            return verdict
    return None


def get_homeworks(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=headers, params=payload)
    except requests.ConnectionError as e:
        error = logging.error(
            'Ошибка соединения. Проверьте подключение'
            ' к интернету. \n\nОшибка: ' + str(e))
        print(str(e))
    except requests.Timeout as e:
        error = logging.error('Время ожидания истекло. \n\nОшибка: ' + str(e))
        send_message(error)
    except requests.RequestException as e:
        error = logging.error('Общая ошибка:\n\n' + str(e))
        send_message(error)

    try:
        result = homework_statuses.json()
        logging.debug(f'Запрос вернул следующий ответ {result}')
    except ValueError:
        error = logging.error(
            'Не удастся десериализовать JSON'
            'полученный из запроса.')
        send_message(error)
    return result


def send_message(message):
    logging.info('Бот отправил сообщение юзеру')
    return bot.send_message(CHAT_ID, message)


def main():
    logging.debug('Бот запущен')
    current_timestamp = int(time.time())

    sent_message = ''
    while True:
        try:
            homework = get_homeworks(current_timestamp)
            current_timestamp = homework['current_date']
            if homework['homeworks']:
                homework = homework['homeworks'][0]
                message = parse_homework_status(homework)
            elif len(homework['homeworks']) == 0:
                message = 'Нет работ доступных к рассмотрению'
            else:
                message = parse_homework_status(homework)

            if sent_message != message:
                send_message(message)
                sent_message = message
            time.sleep(MIN_5)
        except Exception as e:
            logging.error(f'Бот упал с ошибкой: {e}')
            send_message(f'Бот упал с ошибкой: {e}')
            time.sleep(SEC_5)


if __name__ == '__main__':
    main()
