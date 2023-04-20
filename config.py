# ------------------------------------------------------------
# Конфигурация бота
# ------------------------------------------------------------

import os

PROJECT_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE_NAME = os.path.join(PROJECT_ROOT_DIR, "bot_sqlite.db")

_TOKEN_FILE_NAME = os.path.join(PROJECT_ROOT_DIR, "token.txt")
BOT_TOKEN = None

try:
    with open(_TOKEN_FILE_NAME, "r") as f:
        BOT_TOKEN = f.readline().strip()
except Exception:
    print("Ошибка чтениия файла с токеном доступа к telegram боту: " + _TOKEN_FILE_NAME)
    raise
