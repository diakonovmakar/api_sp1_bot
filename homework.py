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

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename='main.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    try:
        homework_instance = homework['homeworks'][0]
    except KeyError:
        homework_instance = homework
    except IndexError:
        return 'Нет работ доступных к рассмотрению'
    homework_name = homework_instance['homework_name']
    if homework_instance['status'] == 'reviewing':
        return f'Ваша работа {homework_name} принята. Ждём ревью.'
    if homework_instance['status'] == 'rejected':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    url = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    homework_statuses = requests.get(url, headers=headers, params=payload)
    logging.debug(f'Запрос вернул следующий ответ {homework_statuses.json()}')
    return homework_statuses.json()


def send_message(message):
    logging.info('Бот отправил сообщение юзеру')
    return bot.send_message(CHAT_ID, message)


"""         if current_homework != homework:
                homework = current_homework
            else:
                logging.debug('Изменений нет')
                time.sleep(5)
                continue"""


def main():
    logging.debug('Бот запущен')
    current_timestamp = int(time.time())  # Начальное значение timestamp
    current_homework_status = ''
    while True:
        try:
            homework = get_homeworks(current_timestamp)
            message = parse_homework_status(homework)
            if current_homework_status != message:
                send_message(message)
                current_homework_status = message
            time.sleep(15 * 60)  # Опрашивать раз в пять минут
        except Exception as e:
            logging.error(f'Бот упал с ошибкой: {e}')
            send_message(f'Бот упал с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
