import logging
import os
import requests
import time
import sys

import telegram
from http import HTTPStatus

from exceptions import EmptyAPIResponse, \
    TelegramMessageError, \
    UnsetTokensError, \
    InvalidResponseAPI, \
    InvalidResponseError

from dotenv import load_dotenv

from logging import StreamHandler
from logging.handlers import RotatingFileHandler

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[StreamHandler(sys.stdout), RotatingFileHandler('my_logger.log', maxBytes=50000000, backupCount=5)])


def check_tokens():
    """Проверка доступности необходимых токенов."""
    for token in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        if token is None:
            logging.critical(
                'Отсутствует обязательная переменная окружения: '
                f'"{token}"!')
    is_all_tokens_present = all([TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID])
    if not is_all_tokens_present:
        raise UnsetTokensError('Отсутствует один или несколько токенов.')


def send_message(bot, message):
    """Отправка сообщений в бот."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Удачная отправка сообщения!')
    except Exception as error:
        logging.error(f'Cообщение не отправлено! {error}')
        raise TelegramMessageError(f'Сообщение не было отправлено! {error}')


def get_api_answer(timestamp):
    """Проверка запроса к единственному эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
        raise InvalidResponseAPI(f'Ошибка при запросе к основному API: {error}')

    if response.status_code != HTTPStatus.OK:
        raise InvalidResponseError(f'Недопустимый статус кода {response.status_code}')

    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации"""
    if isinstance(response, dict):
        try:
            homeworks = response.get('homeworks')
        except Exception as error:
            logging.error(f'Ошибка при запросе к основному API: {error}')
            raise InvalidResponseAPI(f'Ошибка при запросе к основному API: {error}')

        if not isinstance(homeworks, list):
            raise TypeError('Ошибка типа ответа API')
        if 'current_date' not in response:
            raise EmptyAPIResponse('Пустой ответ API')
        return
    raise TypeError('Ошибка типа ответа API')


def parse_status(homework):
    """Извлечение информации о конкретной домашней работе, статус этой работы."""
    homework_name = homework.get('homework_name')
    if 'homework_name' not in homework:
        raise KeyError('В ответе отсутсвует ключ homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус работы - {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            answer = get_api_answer(timestamp)
            check_response(answer)
            homeworks = answer.get('homeworks')
            for homework in homeworks:
                homework_status = parse_status(homework)
                send_message(bot, homework_status)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
