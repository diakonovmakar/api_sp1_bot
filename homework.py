import json
import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    # filename='main.log'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def send_message(bot, message):
    """Отправляет сообщение в бот."""
    try:
        logging.info(f'Бот отправил сообщение юзеру "{message}"')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(f'Бот не отправил сообщение юзеру из-за ошибки: {error}')


def get_api_answer(current_timestamp):
    """Получате ответ от API."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS, params=params)
        if homework_statuses.status_code == 200:
            result = homework_statuses.json()
            logging.debug(f'Запрос вернул следующий ответ {result}')
            return result
        else:
            raise ConnectionError('Ошибка при запросе к эндпоинту.')
    except requests.RequestException as e:
        error = ('Ошибка:\n\n' + str(e))
        logging.error(error)
        return {}
    except json.decoder.JSONDecodeError as e:
        error = (
            'Не удастся десериализовать JSON'
            'полученный из запроса.'
            f'\n\nОшибка: {str(e)}')
        logging.error(error)
        return {}


def check_response(response):
    """Проверяет ответ от API на соответствие ожидаемым требованиям."""
    if not isinstance(response['homeworks'], list):
        logging.error('Возвращаемые работы должны быть списком.')
        raise TypeError('Возвращаемые работы должны быть списком.')
    if response['homeworks'] is None:
        logging.error('Нет списка возвращаемых работ')
        raise KeyError('Нет списка возвращаемых работ')
    return response['homeworks']


def parse_status(homework):
    """Парсит домашку и возвращает вердикт."""
    homework_name = homework['homework_name']
    homework_status = homework['status']

    try:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError:
        error_msg = (f'Незадокументированный статус домашней работы, '
                     f'обнаруженный в ответе API {homework_status}')
        logging.error(error_msg)
        raise KeyError(error_msg)
    finally:
        logging.info(f'У работы {homework_name} статус {homework_status}')
    return None


def check_tokens():
    """Проверяет существование необходимых переменных окружения."""
    error_msg = 'Отсутствует обязательная переменная окружения:'
    if PRACTICUM_TOKEN is None:
        logging.critical(f'{error_msg} "PRACTICUM_TOKEN".')
        return False
    if TELEGRAM_TOKEN is None:
        logging.critical(f'{error_msg} "TELEGRAM_TOKEN".')
        return False
    if TELEGRAM_CHAT_ID is None:
        logging.critical(f'{error_msg} "TELEGRAM_CHAT_ID".')
        return False
    return True


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        logging.debug('Бот запущен')
        current_timestamp = 0
        sent_message = None
        while True:
            try:
                response = get_api_answer(current_timestamp)
                homeworks = check_response(response)
                homework = homeworks[0]
                message = parse_status(homework)

                current_timestamp = response['current_date']
                if sent_message != message:
                    send_message(bot, message)
                    sent_message = message
                time.sleep(RETRY_TIME)

            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                logging.error(f'Бот упал с ошибкой: {error}')
                if sent_message != message:
                    send_message(bot, message)
                    sent_message = message
                time.sleep(RETRY_TIME)
    else:
        logging.debug('Работа бота остановлена.')


if __name__ == '__main__':
    main()
