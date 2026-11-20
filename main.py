import os

from dotenv import load_dotenv
from gigachat import GigaChat
from pathlib import Path

# Загружаем настройки из файла .env
load_dotenv()

# Получаем ключ авторизации
credentials = os.getenv("GIGACHAT_CREDENTIALS")

if not credentials:
    raise ValueError("Не найден ключ GigaChat в файле .env")


# Подключаемся к GigaChat и запрашиваем список моделей
print("Подключаемся к GigaChat...")


CERT_PATH = Path(__file__).with_name("russian_trusted_root_ca_pem.crt")

with GigaChat(
    credentials=credentials,
    ca_bundle_file=str(CERT_PATH),
    model="GigaChat-2"
) as giga:

    print("Подключение успешно!")

    # Отправляем первое сообщение модели
    response = giga.chat.create(
        "Привет! Я разрабатываю ИИ-помощника "
        "для абитуриентов. Кратко расскажи, чем ты можешь "
        "помочь в выборе образовательной программы."
    )

    # Выводим ответ
    answer = response.messages[0].content[0].text

    print("\nОтвет GigaChat:")
    print(answer)