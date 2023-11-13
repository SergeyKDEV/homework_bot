# homework_bot - статус домашней работы

Телеграм бот для проверки статуса домашнего задания на курсе **Yandex.Practicum**.

Работает на базе _**[«API сервиса Практикум.Домашка»](https://code.s3.yandex.net/backend-developer/%D0%9F%D1%80%D0%B0%D0%BA%D1%82%D0%B8%D0%BA%D1%83%D0%BC.%D0%94%D0%BE%D0%BC%D0%B0%D1%88%D0%BA%D0%B0%20%D0%A8%D0%BF%D0%B0%D1%80%D0%B3%D0%B0%D0%BB%D0%BA%D0%B0.pdf)**_

## Установка

Для корректной работы необходимо:
- _**[получить токен](https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a)**_ Яндекс-практикума;
- _**[создать](https://t.me/BotFather)**_ Telegram-бота и получить его токен;
- _**[получить ID](https://t.me/userinfobot)**_ своего аккаунта Telegram.


  **`ВНИМАНИЕ:`НЕ ДОПУСКАЙТЕ РАСПРОСТРАНЕНЕИЯ СВОИХ ТОКЕНОВ!**


1) Клонировать проект:
```Bash
git clone git@github.com:SergeyKDEV/homework_bot.git
```

2) Подготовить виртуальное окружение:

```Bash
# Установка виртуального окружения:

# Для Linux/MacOS
python3 -m venv venv

# Для Windows
python -m venv venv

# Активация виртуального окружения:
source venv/bin/activate

# Обновление pip
python -m pip install --upgrade pip 

# Установка зависимостей
pip install -r requirements.txt

```
3) Импортировать полученные токены в виртуальное окружение:
- Для Linux/MacOS:
```Bash
export PRACTICUM_TOKEN=<PRACTICUM_TOKEN>
export TELEGRAM_TOKEN=<TELEGRAM_TOKEN>
export CHAT_ID=<CHAT_ID>
```
- _**[Инструкция для windows](https://www3.ntu.edu.sg/home/ehchua/programming/howto/Environment_Variables.html)**_

  - Или создать файл `.env` в корне проекта, добавив в него токены. 

4) Запустить проект:
```Bash
python homework.py
```

## Дополнительные настройки

Переменная `RETRY_PERIOD` отвечает за частоту обновления статуса (в секундах).

По умолчанию установлено значение 600 секунд.
Может быть изменено при необходимости.

##
- Автор: _**[Яндекс.Практикум](https://practicum.yandex.ru/)**_

- Разработчик: _**[Кульбида Сергей](https://github.com/SergeyKDEV)**_