import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
import telegram.ext
from dotenv import load_dotenv

from custom_exceptions import (ApiAnswerNot200Error,
                               TokensCheckError,
                               UnexpectedResponseError,
                               UnexpectedStatusError,
                               EmptyHomeworkError)

load_dotenv()

PRACTICUM_TOKEN: str = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(funcName)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(filename=__file__ + '.log')
    ]
)

logger = logging.getLogger(__name__)


def check_tokens() -> None:
    """Проверка переменных окружения."""
    tokens: tuple = (
        (PRACTICUM_TOKEN, 'PRACTICUM_TOKEN'),
        (TELEGRAM_TOKEN, 'TELEGRAM_TOKEN'),
        (TELEGRAM_CHAT_ID, 'TELEGRAM_CHAT_ID'),
    )
    flag: bool = True

    for token_value, token_name in tokens:
        if not token_value:
            flag = False
            logger.critical(
                'Отсутствует обязательная '
                'переменная окружения: "{}"'.format(token_name)
            )
    if not flag:
        raise TokensCheckError()


def send_message(bot: telegram.Bot, message: str) -> bool:
    """Отправляет сообщение в Telegram чат."""
    try:
        logger.debug('Попытка отправки сообщения')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.debug(f'Сообщение успешно отправлено: {message}')
        return True
    except telegram.TelegramError as error:
        logger.error(f'Ошибка отправки сообщения: {error}')
        return False


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к эндпойнту."""
    data: dict = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'payload': {'from_date': timestamp},
    }
    logger.debug('''
    Попытка запроса к API: {}.
    Заголовок запроса: {}.
    Параметры запроса: {}'''.format(*data.values())
                 )
    try:
        response: requests.Response = requests.get(
            url=data.get('url'),
            headers=data.get('headers'),
            params=data.get('payload')
        )
        if response.status_code != HTTPStatus.OK:
            raise ApiAnswerNot200Error('''
            Ошибка запроса к API:
            Код ошибки: {}.
            Попытка запроса к API: {}.
            Заголовок запроса: {}.
            Параметры запроса: {}'''.format(
                response.status_code,
                *data.values(),
            )
            )
        return response.json()
    except requests.RequestException:
        raise ConnectionError('''Ошибка доступа к API (RequestException):
        Попытка запроса к API: {}.
        Заголовок запроса: {}.
        Параметры запроса: {}'''.format(*data.values())
                              )


def check_response(response: dict) -> list:
    """Выполняет валидацию ответа на соответствие документации."""
    logger.debug('Начата проверка ответа API')

    if not isinstance(response, dict):
        type_error_msg = 'Неверный тип данных переменной "response"'
        logger.error(type_error_msg)
        raise TypeError(type_error_msg)

    if 'homeworks' not in response.keys():
        type_error_msg = 'В ответе API отсутствует ключ "homeworks"'
        logger.error(type_error_msg)
        raise EmptyHomeworkError(type_error_msg)

    homework: list = response.get('homeworks')

    if not isinstance(homework, list):
        type_error_msg = 'В ответе API получен неверный тип данных'
        logger.error(type_error_msg)
        raise TypeError(type_error_msg)

    return homework


def parse_status(homework: dict) -> str:
    """Возвращает статус домашней работы."""
    homework_name: str = homework.get('homework_name')
    status: str = HOMEWORK_VERDICTS.get(homework.get('status'))
    if not homework_name:
        parse_status_msg = 'В ответе отсутствует ключ "homework_name"'
        logger.error(parse_status_msg)
        raise UnexpectedStatusError(parse_status_msg)
    if not status:
        parse_status_msg = 'В ответе отсутствует ключ "status"'
        logger.error(parse_status_msg)
        raise UnexpectedStatusError(parse_status_msg)
    return f'Изменился статус проверки работы "{homework_name}". {status}'


def main():
    """Основная логика работы бота."""
    logger.debug('Запуск')

    if check_tokens():
        exit()

    timestamp: int = int(time.time())
    last_status: str = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    last_error: str = ''

    while True:
        try:
            response: dict = get_api_answer(timestamp)
            if check_response(response):
                last_homework: dict = response.get('homeworks')[0]
                current_status: str = last_homework.get('status')
                if last_status != current_status:
                    message: str = parse_status(last_homework)
                    send_message(bot, message)
                    last_status = current_status
                else:
                    logger.debug('Статус домашней работы не изменился')
        except Exception as error:
            error_msg = f'Сбой в работе программы: "{error}"'
            logger.error(error_msg)
            if error_msg != last_error:
                send_message(bot, error_msg)
                last_error = error_msg
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
