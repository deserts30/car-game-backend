import random

# Цвета и их множитель цены
COLORS = {
    "Чёрный": 1.0,
    "Белый": 1.05,
    "Серебристый": 1.1,
    "Красный": 1.15,
    "Синий": 1.12,
    "Жёлтый": 1.3,
    "Хамелеон": 1.8,
    "Матовый чёрный": 1.5,
}

# Марка: (множитель, базовая цена)
BRANDS = {
    "Lada": (0.3, 10000),
    "Toyota": (1.0, 30000),
    "BMW": (1.5, 60000),
    "Mercedes": (1.6, 65000),
    "Porsche": (2.5, 150000),
    "Ferrari": (4.0, 400000),
    "Lamborghini": (3.5, 350000),
    "Bugatti": (8.0, 2000000),
}

RARITY_MULT = {
    "common": 1.0,
    "rare": 1.5,
    "epic": 2.5,
    "legendary": 5.0,
}


def calculate_price(brand, year, color, rarity, condition=100):
    """Считает итоговую цену машины."""
    base = BRANDS.get(brand, (1.0, 20000))[1]

    # Год: чем новее, тем дороже. Ретро (>30 лет) тоже ценится
    age = 2025 - year
    year_mult = max(0.4, 1.0 - age * 0.02)
    if age > 30:
        year_mult += 0.5

    color_mult = COLORS.get(color, 1.0)
    rarity_mult = RARITY_MULT.get(rarity, 1.0)
    cond_mult = condition / 100

    return round(base * year_mult * color_mult * rarity_mult * cond_mult, 2)


def roll_car():
    """Выбивает случайную машину."""
    roll = random.random()
    if roll < 0.55:
        rarity = "common"
    elif roll < 0.85:
        rarity = "rare"
    elif roll < 0.97:
        rarity = "epic"
    else:
        rarity = "legendary"

    brand = random.choice(list(BRANDS.keys()))
    year = random.randint(1985, 2025)
    color = random.choices(
        list(COLORS.keys()),
        weights=[15, 12, 12, 10, 10, 5, 2, 3],
        k=1
    )[0]
    condition = random.randint(60, 100)

    price = calculate_price(brand, year, color, rarity, condition)

    return {
        "brand": brand,
        "model": "",
        "year": year,
        "color": color,
        "rarity": rarity,
        "condition": condition,
        "price": price,
    }
