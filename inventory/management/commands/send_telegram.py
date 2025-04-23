import asyncio
from django.core.management.base import BaseCommand
from telegram import Bot

class Command(BaseCommand):
    help = 'Отправка уведомления в Telegram'

    def handle(self, *args, **options):
        token = '7547749911:AAHSSR68zLuMndKxvzqXLxlSwJ8_kTdXf1g'
        chat_id = '1236410913'
        message = '📦 Ингредиенты на складе закончились!'

        async def send():
            bot = Bot(token=token)
            await bot.send_message(chat_id=chat_id, text=message)

        asyncio.run(send())
        self.stdout.write(self.style.SUCCESS('✅ Уведомление отправлено'))
