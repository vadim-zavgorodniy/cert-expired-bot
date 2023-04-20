# CertExpiredBot (Your Cert Expired Notification Bot)

## Описание
Telegram bot для напоминания о своевременном перевыпуске TLS (SSL)
сертификатов.

## Настройка и запуск
Токен доступа к telegram боту должен быть в каталоге с проектом в
первой строке файла token.txt

Для работы потребуются установленные python3 и pip.

После клонирования репозитория создайте виртуальное окружение.
В каталоге проекта и установите необходимые зависимости:
```shell
$ python3 -m venv .venv
$ source .venv/bin/activate
(.venv) $ pip install -r requirements.txt
```
Для запуска введите
```shell
$ python3 main.py
```

Для выхода из виртуального окружения проекта введите:
```shell
(.venv) $ deactivate
```
