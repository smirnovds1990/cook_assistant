# Foodgram (Продуктовый помощник)
Проект "Продуктовый помощник" - это сайт для выкладывания рецептов. Пользователь регистрируется на сайте, может создавать рецепты, добавлять их в избранное, подписываться на других пользователей. Так же есть возможность добавить рецепты в список покупок, из которого потом можно скачать файл со списком продуктов.

https://somedomainname.ddns.net/

Данные администратора:
email - superuser@mail.ru
password - 789asd456asd

### Технологии
- Nginx
- Django
- Django REST framework
- Gunicron
- Python
- Docker
- JavaScript
- React

### Установка
Склонировать репозиторий
```
git clone https://github.com/smirnovds1990/foodgram-project-react
```
Установка [Docker](https://www.docker.com/get-started/) - перейдите по ссылке, следуйте инструкциям в зависимости от вашей ОС.
После установки Docker:
 - Открыть Docker Desktop
- Запустить сборку контейнеров:
```
docker compose up
```
либо
```
docker compose -f docker-compose.production.yml up
```
Простая команда `docker compose up` запускает сборку, следуя инструкции в файле по умолчанию - `docker-compose.yml`, используя Docker-файлы, находящиеся в директориях backend, frontend, nginx.

Команда с опциями `docker compose -f docker-compose.production.yml up` запускает сборку из файла `docker-compose.production.yml`, следуя инструкции которого, образы подгружаются с DockerHub, а не создаются локально.

###### Сделать миграции и собрать статику (в новом окне терминала):

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /kittygram_app/collected_static/. /backend_static/static
```

###### Импортировать ингридиенты из csv файла(в новом окне терминала):

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_data /data/ingridients.csv
```

###### Создать суперюзера(в новом окне терминала):

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

После создания суперюзера, зайти в админ-панель и создать теги (их можно создавать только через админку).

**Если сборка запускается командой docker compose up, использовать команды для сборки статики и миграции без опции -f docker-compose.production.yml**

Перейти на сайт http://localhost:8000/

## Работа со скрытыми переменными

Для работы со скрытыми переменными используется библиотека python-decouple. [Ссылка на документацию](https://pypi.org/project/python-decouple/)

Скрытые переменные хранятся в файле .env в корневой директории проекта. Пример файла приведён в данной директории в файле .env.example.
```
DEBUG = True
SECRET_KEY = 'My_Secret_Key'
ALLOWED_HOSTS = 127.0.0.1, localhost
```
В файле настроек вызываются следующим образом:
```
from decouple import config, Csv
...
SECRET_KEY = config('SECRET_KEY', default='mykey')
DEBUG = config('DEBUG', cast=bool, default=False)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default='localhost')
```
Более подробную информацию по работе с библиотекой можно найти в документации по ссылке выше.


###### Автор проекта
[smirnovds](https://github.com/smirnovds1990)
