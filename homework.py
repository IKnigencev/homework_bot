"""Основной модуль бота."""
from http import HTTPStatus
import os
import time
import requests
import logging
from dotenv import load_dotenv

import telegram


from exceptions import IncorrectStatusResponse


load_dotenv()


logging.basicConfig(
    filename='logg.log',
    format='%(asctime)s, %(levelname)s, %(message)s',
    filemode='a',
    level=logging.ERROR
)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_TIME = 1
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Функция отправки сообщений."""
    try:
        logging.info('Отправка сообщения в чат.')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    """Функция запроса к внешнему API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logging.info('Отправка запроса к API.')
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        raise IncorrectStatusResponse(response)
    try:
        return response.json()
    except Exception as error:
        logging.error(f'Ответ пришел не в виде json: {error}')


def check_response(response: dict) -> dict:
    """Функция проверки результата ответа от API."""
    if isinstance(response, dict):
        try:
            result = response.get('homeworks')
            if result is None:
                message = f'Отсутствует ключ в ответе {response}'
                raise KeyError(message)
            elif not isinstance(result, list):
                message = f'Ответ пришел не в виде списка: {type(result)}'
                raise TypeError(message)
            message = f'Ответ пришел в корректном виде {type(result)}'
            logging.info(message)
            return result
        except TypeError as error:
            logging.error(error)
            raise TypeError(error)
    return response


def parse_status(homework):
    """Получение резуьтата из response."""
    if isinstance(homework, dict):
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[f'{homework_status}']
        message = (f'Изменился статус проверки работы "{homework_name}".'
                   f'{verdict}')
        return message
    else:
        message = 'Ошибка при попытке достать ответ из response'
        raise Exception(message)


def check_tokens() -> bool:
    """Проверка необходимых ключей."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    status = ''
    error_cache = ''
    logging.info('Проверка статуса токенов.')
    if not check_tokens():
        logging.critical('Отсутствуют одна или несколько переменных окружения')
        raise Exception('Отсутствуют одна или несколько переменных окружения')
    while True:
        try:
            logging.info('Запуска основной части main.')
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            homework = check_response(response)
            message = parse_status(homework[0])
            if message != status:
                send_message(bot, message)
                status = message
        except Exception as error:
            message_error = f'Сбой в работе программы: {error}'
            logging.error(message_error)
            if message_error != error_cache:
                send_message(bot, message_error)
                error_cache = message_error
        else:
            logging.info('Ожидание сделующего завроса.')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
