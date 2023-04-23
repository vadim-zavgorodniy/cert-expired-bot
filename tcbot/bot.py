"""Основной модуль с логикой работы бота."""


from functools import wraps
from typing import Callable, TypeVar
from typing_extensions import ParamSpec
import telebot
from telebot.types import Message

from tcbot import config
from tcbot.storage import CertStore, CertModel, ParseError

from tcbot.logger import get_logger

_logger = get_logger(__name__)
_bot = telebot.TeleBot(config.BOT_TOKEN)

_ADD_NEW_CERT_TEXT = """Введите данные о сертификате в формате
date; common_name; description
Например:
10.08.2023; test.my-domain.ru; TLS сертификат тестового домена"""


RetT = TypeVar("RetT")
ArgT = ParamSpec("ArgT")


# ------------------------------------------------------------
def log_error(func: Callable[ArgT, None]) -> Callable[ArgT, None]:
    """Декоратор для логирования исключений. Исключения поглощаются декоратором."""
    @wraps(func)
    def log_error_decorator(*args: ArgT.args, **kwargs: ArgT.kwargs) -> None:
        try:
            func(*args, **kwargs)
        except Exception as exc: # pylint: disable=broad-exception-caught
            _logger.exception("%s Ошибка при работе с меню: %s", type(exc), exc)

    return log_error_decorator


# ------------------------------------------------------------
@log_error
def run_bot() -> None:
    """Основная функция запускающая работу бота."""
    _bot.polling(none_stop=True, interval=0)


# ------------------------------------------------------------
def _get_cert_store() -> CertStore:
    """Возвращает новый экземпляр для рабты с хранилищем сертификатов CertStore"""
    return CertStore(config.DB_FILE_NAME)


# ------------------------------------------------------------
@_bot.message_handler(content_types=["text"])
@log_error
def _start(message: Message) -> None:
    """Функция начала работы с ботом. Выводит меню доступных команд."""
    with _get_cert_store() as store:
        if message.text == "/list":
            cert_list = store.find_all_certs(message.from_user.id)
            if len(cert_list) == 0:
                _bot.send_message(
                    message.from_user.id,
                    "Вы еще не добавили ни одного сертификата.\n" +
                    "Для добавления введите /add")
            else:
                result = CertModel.list_to_string_list(cert_list)
                _bot.send_message(message.from_user.id, "\n".join(result))
        elif message.text == "/add":
            _bot.send_message(message.from_user.id, _ADD_NEW_CERT_TEXT)
            _bot.register_next_step_handler(
                message, _add_cert)  # следующий шаг – функция add_cert
        elif message.text == "/del":
            _bot.send_message(message.from_user.id,
                              "Для удаления укажите common name сертификата.")
            _bot.register_next_step_handler(
                message, _del_cert)  # следующий шаг – функция del_cert
        else:
            _bot.send_message(message.from_user.id,
                              "Доступные команды: /list /add /del")


# ------------------------------------------------------------
@log_error
def _add_cert(message: Message) -> None:
    """Добавляет данные сертификата пользователя в хранилище"""
    new_cert: CertModel
    try:
        new_cert = CertModel.from_string(message.text)
    except ParseError as exc:
        _bot.send_message(message.from_user.id,
                          f"Проблема :(\n{exc}\n" + _ADD_NEW_CERT_TEXT)
        return

    with _get_cert_store() as store:
        rows = store.find_by_cn(message.from_user.id, new_cert.common_name)
        if len(rows):
            _bot.send_message(
                message.from_user.id,
                "Похоже, что такой сертификат уже учтен. Можно его удалить - /del\n" +
                str(rows[0]))
        else:
            new_cert.user_id = message.from_user.id
            store.add_cert(new_cert)
            _bot.send_message(message.from_user.id,
                              "Данные сохранены:\n" + message.text)


# ------------------------------------------------------------
@log_error
def _del_cert(message: Message) -> None:
    """Удаляет данные сертификата пользователя из хранилищащ"""
    with _get_cert_store() as store:
        rows = store.find_by_cn(message.from_user.id, message.text.strip())
        if len(rows) == 0:
            _bot.send_message(
                message.from_user.id, "Сертификат с таким CN не найден. " +
                "Можно проверить его наличие с помощью /list")
        else:
            assert rows[0].rec_id is not None
            store.delete_cert(message.from_user.id, rows[0].rec_id)
            _bot.send_message(message.from_user.id, "Данные удалены:\n" + str(rows[0]))
