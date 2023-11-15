class TokensCheckError(Exception):
    """Ошибка проверки токенов."""


class ApiAnswerNot200Error(Exception):
    """Код ответа сервера API отличен от 200."""


class UnexpectedResponseError(Exception):
    """Получен неверный формат ответа API."""


class UnexpectedStatusError(Exception):
    """Неожиданный статус домашней работы."""
