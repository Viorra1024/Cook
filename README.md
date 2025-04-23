# 🧑‍🍳 ChefCook — Система управления кухней

ChefCook — это веб-приложение для ресторанов и кафе, позволяющее:
- Хранить рецепты с пошаговыми инструкциями
- Управлять запасами продуктов
- Планировать меню на день и неделю
- Автоматически рассчитывать нужные ингредиенты
- Создавать заказы у поставщиков
- Получать уведомления в Telegram при нехватке ингредиентов

---

## 🚀 Установка и запуск

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/yourusername/chefcook.git
cd chefcook


2. Создайте виртуальное окружение (рекомендуется)
bash
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate   # macOS / Linux


3. Установите зависимости
bash
pip install -r requirements.txt


4. Настройте базу данных PostgreSQL
Создайте базу и пользователя:

sql
CREATE DATABASE chef_cook_db;
CREATE USER chefuser WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE chef_cook_db TO chefuser;
Обновите settings.py:

python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'chef_cook_db',
        'USER': 'chefuser',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


5. Примените миграции
bash
python manage.py makemigrations
python manage.py migrate


6. Создайте администратора
bash
python manage.py createsuperuser


7. Запустите сервер
bash
python manage.py runserver
Откройте: http://127.0.0.1:8000/

📦 Зависимости
Django 5.x

PostgreSQL

python-telegram-bot

Celery + Redis (опционально)

Bootstrap 5

Установите с помощью:


bash
pip install -r requirements.txt
📲 Уведомления Telegram
Создайте бота через @BotFather

Вставьте токен в send_telegram.py

Используйте команду:

bash
python manage.py send_telegram
🛠️ Авторы и разработка
Проект разрабатывается в рамках учебной и практической деятельности.

Автор: [Ваше имя]
Контакты: [email@example.com]
