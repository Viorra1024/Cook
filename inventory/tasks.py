from celery import shared_task
from .models import Ingredient
from celery.schedules import crontab
from celery import Celery


@shared_task
def restock_ingredients():
    ingredients = Ingredient.objects.all()
    restock_list = []

    for ingredient in ingredients:
        if ingredient.quantity < 10:  # Если меньше 10 единиц, пополняем
            ingredient.quantity += 50  # Добавляем 50 единиц
            ingredient.save()
            restock_list.append({"ingredient": ingredient.name, "new_quantity": ingredient.quantity})

    return restock_list


@shared_task
def check_low_stock():
    low_stock_items = []

    for ingredient in Ingredient.objects.all():
        if ingredient.quantity < 10:  # Если запас < 10, отправляем уведомление
            low_stock_items.append({
                "ingredient": ingredient.name,
                "quantity": ingredient.quantity,
                "unit": ingredient.unit
            })

    if low_stock_items:
        print("🔔 Внимание! Заканчиваются ингредиенты:")
        for item in low_stock_items:
            print(f"⚠ {item['ingredient']}: {item['quantity']} {item['unit']} осталось!")

    return low_stock_items


app = Celery('chef_cook')

app.conf.beat_schedule = {
    'restock-every-12-hours': {
        'task': 'inventory.tasks.restock_ingredients',
        'schedule': crontab(hour='*/12'),
    },
}

app.conf.beat_schedule.update({
    'check-low-stock-every-12-hours': {
        'task': 'inventory.tasks.check_low_stock',
        'schedule': crontab(hour='*/12'),
    },
})
