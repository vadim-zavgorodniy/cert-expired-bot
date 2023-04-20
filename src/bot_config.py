# ------------------------------------------------------------
# Конфигурация бота
# ------------------------------------------------------------

DB_FILE_NAME = "./bot_sqlite.db"
_TOKEN_FILE_NAME = "./token.txt"
BOT_TOKEN = None

try:
    with open(_TOKEN_FILE_NAME, "r") as f:
        BOT_TOKEN = f.readline().strip()
except Exception:
    print("Ошибка чтениия файла с токеном доступа к telegram боту: " +
          _TOKEN_FILE_NAME)
    raise
