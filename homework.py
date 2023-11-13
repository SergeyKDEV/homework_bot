import logging
import os
import time

import requests
import telegram
import telegram.ext
from dotenv import load_dotenv

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


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class ApiAnswerNot200Error(Exception):
    """Код ответа сервера API отличен от 200."""


class RequestExceptionError(Exception):
    """Ошибка запроса к серверу API."""


class UnexpectedResponseError(Exception):
    """Получен неверный формат ответа API."""


class UnexpectedStatusError(Exception):
    """Неожиданный статус домашней работы."""


def check_tokens() -> bool:
    """Проверка переменных окружения."""
    token_error_msg = "Отсутствует обязательная переменная окружения: '{}'"
    flag: bool = True
    if not PRACTICUM_TOKEN:
        flag = False
        logger.critical(token_error_msg.format('PRACTICUM_TOKEN'))
    elif not TELEGRAM_TOKEN:
        flag = False
        logger.critical(token_error_msg.format('TELEGRAM_TOKEN'))
    elif not TELEGRAM_CHAT_ID:
        flag = False
        logger.critical(token_error_msg.format('TELEGRAM_CHAT_ID'))
    return flag


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.debug('Сообщение успешно отправлено')
    except telegram.TelegramError as error:
        logger.error(f'Ошибка отправки сообщения: {error}')


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к эндпойнту."""
    # payload: dict = {'from_date': timestamp - 914_400 * CHECK_TIME_DAYS}
    payload: dict = {'from_date': timestamp}
    try:
        response: requests.Response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=payload)
        if response.status_code != 200:
            endpoint_error_msg: str = (f'Сбой в работе программы: '
                                       f'Эндпоинт {ENDPOINT} недоступен. '
                                       f'Код ответа API: '
                                       f'{response.status_code}')
            logger.error(endpoint_error_msg)
            raise ApiAnswerNot200Error(endpoint_error_msg)
        return response.json()
    except requests.exceptions.RequestException as request_exception:
        get_api_answer_msg = (f'Ошибка доступа к API '
                              f'(RequestException): {request_exception}.')
        logger.error(get_api_answer_msg)
        raise RequestExceptionError(get_api_answer_msg)


def check_response(response: dict) -> bool:
    """Выполняет валидацию ответа на соответствие документации."""
    if type(response) is not dict:
        type_error_msg = "Неожиданный тип данных переменной 'response'"
        logger.error(type_error_msg)
        raise TypeError(type_error_msg)
    else:
        homework: list = response.get('homeworks')

    if type(homework) is not list:
        type_error_msg = 'В ответе API получен неверный тип данных'
        logger.error(type_error_msg)
        raise TypeError(type_error_msg)
    elif not homework:
        type_error_msg = 'В ответе отсутствует ожидаемый ключ'
        logger.error(type_error_msg)
        raise UnexpectedResponseError(type_error_msg)
    else:
        return homework and response.get('current_date')


def parse_status(homework: dict) -> str:
    """Возвращает статус домашней работы."""
    homework_name: str = homework.get('homework_name')
    status: str = HOMEWORK_VERDICTS.get(homework.get('status'))
    if not homework_name:
        parse_status_msg = "В ответе отсутствует ключ 'homework_name'"
        logger.error(parse_status_msg)
        raise UnexpectedStatusError(parse_status_msg)
    if not status:
        parse_status_msg = "В ответе отсутствует ключ 'status'"
        logger.error(parse_status_msg)
        raise UnexpectedStatusError(parse_status_msg)
    return f'Изменился статус проверки работы "{homework_name}". {status}'


def main():
    """Основная логика работы бота."""
    logger.debug('Запуск')

    if not check_tokens():
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
            error_msg = f'Сбой в работе программы: {error}'
            logger.error(error_msg)
            if error_msg != last_error:
                send_message(bot, error_msg)
                last_error = error_msg
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
