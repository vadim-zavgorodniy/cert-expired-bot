import telebot
from telebot import types

from functools import wraps

import bot_config as conf
from storage import CertStore, CertModel, ParseError

bot = telebot.TeleBot(conf.BOT_TOKEN)

_ADD_NEW_CERT_TEXT = """Введите данные о сертификате в формате
date; common_name; description
Например:
10.08.2023; test.my-domain.ru; TLS сертификат тестового домена"""

def getCertStore():
    return CertStore(conf.DB_FILE_NAME)

# ------------------------------------------------------------
def log_error(func):
    @wraps(func)
    def log_error_decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(str(e.__class__) + ": Ошибка при работе с меню:" + str(e))
    return log_error_decorator

# ------------------------------------------------------------
@bot.message_handler(content_types=["text"])
@log_error
def start(message):
    with getCertStore() as store:
        if message.text == '/list':
            cert_list = store.find_all_certs(message.from_user.id)
            if not len(cert_list):
                bot.send_message(
                    message.from_user.id,
                    "Вы еще не добавили ни одного сертификата.\nДля добавления введите /add"
                )
            else:
                result = CertModel.list_to_string_list(cert_list)
                bot.send_message(message.from_user.id, "\n".join(result))
        elif message.text == '/add':
            bot.send_message(message.from_user.id, _ADD_NEW_CERT_TEXT)
            bot.register_next_step_handler(
                message, add_cert)  #следующий шаг – функция add_cert
        elif message.text == '/del':
            bot.send_message(message.from_user.id,
                             "Для удаления укажите common name сертификата.")
            bot.register_next_step_handler(
                message, del_cert)  #следующий шаг – функция del_cert
        else:
            bot.send_message(message.from_user.id,
                             "Доступные команды: /list /add /del")

# ------------------------------------------------------------
@log_error
def add_cert(message):  # добавляем данные сертификата
    new_cert = {}
    try:
        new_cert = CertModel.from_string(message.text)
    except ParseError as e:
        bot.send_message(message.from_user.id,
                         "Проблема :(\n{}\n".format(e) + _ADD_NEW_CERT_TEXT)
        return

    with getCertStore() as store:
        rows = store.find_by_cn(message.from_user.id, new_cert.cn)
        if len(rows):
            bot.send_message(
                message.from_user.id,
                "Похоже, что такой сертификат уже учтен. Можно его удалить - /del\n"
                + rows[0])
        else:
            new_cert.user_id = message.from_user.id
            # store.add_cert((message.from_user.id, new_cert.get("cn"), new_cert.get("description"), new_cert.get("exp_date")))
            store.add_cert(new_cert)
            bot.send_message(message.from_user.id,
                             "Данные сохранены:\n" + message.text)


# ------------------------------------------------------------
@log_error
def del_cert(message):  # удаляем сертификат
    with getCertStore() as store:
        rows = store.find_by_cn(message.from_user.id, message.text.strip())
        if not len(rows):
            bot.send_message(
                message.from_user.id,
                "Сертификат с таким CN не найден. Можно проверить его наличие с помощью /list"
            )
        else:
            # cert = CertTools.cert_to_dict(rows[0])
            store.delete_cert(message.from_user.id, rows[0].id)
            bot.send_message(message.from_user.id,
                             "Данные удалены:\n" + str(rows[0]))


# ------------------------------------------------------------
if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
