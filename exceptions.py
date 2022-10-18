"""Собственные исключения."""


class IncorrectStatusResponse(Exception):
    """Обработка ответа API."""

    def __init__(self, response):
        """Проверка статуса кода и сохранение."""
        if response.status_code == 200:
            self.response = response.status_code
            self.status = True
        else:
            self.response = response.status_code
            self.status = False

    def __str__(self):
        """Корректировка вывода ошибки."""
        if self.status:
            message = 'Корректное подключение к API'
            return message
        else:
            message = f'Ошиббка при подключении к API: {self.response}'
            return message
