import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
import telegram.ext
from dotenv import load_dotenv

from custom_exceptions import (ApiAnswerNot200Error, EmptyHomeworkError,
                               TokensCheckError)

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
        logging.FileHandler(filename=__file__ + '.log', encoding='utf-8')
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
        raise TokensCheckError('Ошибка проверки переменных окружения')


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
    request_data: dict = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    logger.debug(
        'Попытка запроса к API: {url}. '
        'Заголовок запроса: {headers}. '
        'Параметры запроса: {params}'.format(**request_data)
    )
    try:
        response: requests.Response = requests.get(**request_data)
        if response.status_code != HTTPStatus.OK:
            raise ApiAnswerNot200Error(
                'Ошибка запроса к API: '
                'Код ошибки: {}. '
                'Причина: {}. '
                'Текст ответа: {}'.format(
                    response.status_code,
                    response.reason,
                    response.text,
                )
            )
        return response.json()
    except requests.RequestException:
        raise ConnectionError(
            'Ошибка доступа к API (RequestException): '
            'Попытка запроса к API: {url}. '
            'Заголовок запроса: {headers}. '
            'Параметры запроса: {params}'.format(**request_data)
        )


def check_response(response: dict) -> list:
    """Выполняет валидацию ответа на соответствие документации."""
    logger.debug('Начата проверка ответа API')

    if not isinstance(response, dict):
        raise TypeError('Неверный тип данных переменной "response"')

    if 'homeworks' not in response.keys():
        raise EmptyHomeworkError('В ответе API отсутствует ключ "homeworks"')

    homework: list = response.get('homeworks')

    if not isinstance(homework, list):
        raise TypeError('В ответе API получен неверный тип данных')

    return homework


def parse_status(homework: dict) -> str:
    """Возвращает статус домашней работы."""
    homework_name: str = homework.get('homework_name')
    status: str = HOMEWORK_VERDICTS.get(homework.get('status'))

    if not all(key in homework for key in ('homework_name', 'status')):
        raise ValueError('В ответе отсутствуют ожидаемые ключи')

    if status not in HOMEWORK_VERDICTS.values():
        raise ValueError('Получен неизвестный статус домашней работы')

    return f'Изменился статус проверки работы "{homework_name}". {status}'


def main() -> None:
    """Основная логика работы бота."""
    logger.debug('Запуск')

    check_tokens()
    logger.debug('Переменные окружения проверены')

    timestamp: int = 0
    last_status: str = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response: dict = get_api_answer(timestamp)
            homeworks: list = check_response(response)

            if homeworks:
                last_homework: dict = homeworks[0]
                current_status: str = parse_status(last_homework)

            if current_status != last_status:
                if send_message(bot, current_status):
                    last_status = current_status
                    timestamp = response.get('current_date', 0)
            else:
                logger.debug(f'Статус домашней работы: {current_status}')

        except EmptyHomeworkError as error:
            logger.error(f'{error}: Пустой ответ API')

        except Exception as error:
            current_status = f'Сбой в работе программы: "{error}"'
            logger.error(current_status, exc_info=True)
            if current_status != last_status:
                send_message(bot, current_status)
                last_status = current_status

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
