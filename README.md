![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)  ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)


# Проект FoodGram позволяет пользователю делиться своими рецептами, а также и просматривать и сохранять к себе рецепты других пользователей. 

## Деплой проекта foodgram в **Docker контейнерах** и CI/CD с помощью GitHub Actions на удалённый сервер 

### Описание проекта

Проект Foodgram - социальная сеть для обмена рецептами любимых блюд.

Это полностью рабочий проект, который состоит из бэкенд-приложения на **Fastapi**

### Возможности проекта: 

Можно зарегистрироваться и авторизоваться, добавить нового котика на сайт или изменить существующего, добавить или изменить достижения, а также просмотреть записи других пользователей.

API для Foodgram написан с использованием библиотеки **FastAPI**, используется **JWTAuthentication** для аутентификации.


### Технологии

- Python 3.9
- FastAPI
- SqlAlchemy


### Запуск проекта в dev-режиме

Клонировать репозиторий и перейти в него в командной строке: 
```
git clone git@github.com:LenarSag/foodgram_fastapi.git
```
Cоздать и активировать виртуальное окружение: 
```
python3.9 -m venv venv 
```
* Если у вас Linux/macOS 

    ```
    source venv/bin/activate
    ```
* Если у вас windows 
 
    ```
    source venv/scripts/activate
    ```
```
python3.9 -m pip install --upgrade pip
```
Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```

Выполнить миграции:


Подключаем и настраиваем алембик:

```
alembic init migration
```

В файле alembic.ini указываем адрес базы:

```
[alembic]
...
sqlalchemy.url = sqlite:///db.sqlite3
```

В файле migration/env.py импортируем все модели и указываем target_metadata:

```
import models

target_metadata = models.Base.metadata
```

После этого:

```
alembic revision --autogenerate -m 'initial'
```
```
alembic upgrade head
```

Запуск проекта:


```
python main.py
```


* Перейти по адресу 127.0.0.1:8000


### Примеры запросов:

# Спецификация

При локальном запуске документация будет доступна по адресу:

```
http://127.0.0.1:8000/api/docs/
```

# Примеры запросов к API

### Регистрация нового пользователя

Описание метода: Зарегистрировать пользователя в сервисе. Права доступа: Доступно без токена.

Тип запроса: `POST`

Эндпоинт: `/api/users/`

Обязательные параметры: `email, username, first_name, last_name, password`

Пример запрос:

```
{
  "email": "vpupkin@yandex.ru",
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов",
  "password": "Qwerty123"
}
```

Пример успешного ответа:

```
{
  "email": "vpupkin@yandex.ru",
  "id": 0,
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов"
}
```

### Cписок тегов

Описание метода: Получение списка тегов. Права доступа: Доступно без токена.

Тип запроса: `GET`

Эндпоинт: `/api/tags/`

Пример запроса:

Пример успешного ответа:

```
[
  {
    "id": 0,
    "name": "Завтрак",
    "slug": "breakfast"
  }
]
```

### Добавление нового рецепта

Описание метода: Добавить новый рецепт. Права доступа: Аутентифицированные пользователи.

Тип запроса: `POST`

Эндпоинт: `/api/recipes/`

Обязательные параметры: `ingredients, tags, image, name, text, cooking_time`

Пример запроса:

```
{
  "ingredients": [
    {
      "id": 1123,
      "amount": 10
    }
  ],
  "tags": [
    1,
    2
  ],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
```

Пример успешного ответа:

```
{
  "id": 0,
  "tags": [
    {
      "id": 0,
      "name": "Завтрак",
      "slug": "breakfast"
    }
  ],
  "author": {
    "email": "user@example.com",
    "id": 0,
    "username": "string",
    "first_name": "Вася",
    "last_name": "Иванов",
    "is_subscribed": false,
    "avatar": "http://foodgram.example.org/media/users/image.png"
  },
  "ingredients": [
    {
      "id": 0,
      "name": "Картофель отварной",
      "measurement_unit": "г",
      "amount": 1
    }
  ],
  "is_favorited": true,
  "is_in_shopping_cart": true,
  "name": "string",
  "image": "http://foodgram.example.org/media/recipes/images/image.png",
  "text": "string",
  "cooking_time": 1
}
```