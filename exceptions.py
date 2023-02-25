class EmptyAPIResponse(Exception):
    """Пустой ответ API"""
    pass


class TelegramMessageError(Exception):
    """Ошибка отправки сообщения в Telegram"""
    pass


class UnsetTokensError(Exception):
    """Отсутствует один или несколько токенов"""
    pass


class InvalidResponseAPI(Exception):
    """ Не удается подключиться к API"""
    pass


class InvalidResponseError(Exception):
    """Не верный код ответа."""
    pass
