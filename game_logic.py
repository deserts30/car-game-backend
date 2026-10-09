import random

COLORS = {
    "Чёрный": 1.0,
    "Белый": 1.05,
    "Серебристый": 1.1,
    "Красный": 1.15,
    "Синий": 1.12,
    "Жёлтый": 1.3,
    "Хамелеон": 1.8,
    "Матовый чёрный": 1.5,
    "Розовый": 1.6,
    "Золотой": 2.2,
    "Радужный": 2.8,
    "Юбилейная": 3.0,
}

# Реалистичные цены в рублях
COUNTRIES = {
    "russia": {
        "name": "🇷🇺 Россия",
        "brands": {
            "Lada": 500_000,
            "GAZ": 450_000,
            "UAZ": 700_000,
            "Moskvich": 350_000,
            "ZIL": 900_000,
            "KAMAZ": 1_500_000,
        },
    },
    "germany": {
        "name": "🇩🇪 Германия",
        "brands": {
            "BMW": 5_000_000,
            "Mercedes": 6_000_000,
            "Audi": 4_500_000,
            "Porsche": 15_000_000,
            "Volkswagen": 2_500_000,
            "Opel": 1_800_000,
        },
    },
    "italy": {
        "name": "🇮🇹 Италия",
        "brands": {
            "Ferrari": 35_000_000,
            "Lamborghini": 30_000_000,
            "Maserati": 15_000_000,
            "Alfa Romeo": 4_000_000,
            "Fiat": 1_200_000,
        },
    },
    "usa": {
        "name": "🇺🇸 США",
        "brands": {
            "Ford": 3_000_000,
            "Chevrolet": 3_500_000,
            "Tesla": 8_000_000,
            "Dodge": 5_000_000,
            "Cadillac": 7_000_000,
            "Jeep": 4_500_000,
        },
    },
    "japan": {
        "name": "🇯🇵 Япония",
        "brands": {
            "Toyota": 3_000_000,
            "Honda": 2_800_000,
            "Nissan": 2_500_000,
            "Mazda": 2_200_000,
            "Subaru": 3_200_000,
            "Lexus": 7_500_000,
        },
    },
    "dubai": {
        "name": "🇦🇪 Дубай",
        "brands": {
            "Bugatti": 200_000_000,
            "Koenigsegg": 180_000_000,
            "Rolls-Royce": 80_000_000,
            "Bentley": 50_000_000,
            "McLaren": 60_000_000,
            "Maybach": 40_000_000,
        },
    },
}

RARITY_MULT = {
    "common": 1.0,
    "rare": 1.5,
    "epic": 2.5,
    "legendary": 5.0,
}

MODIFIERS = [
    ("Ржавая",         0.35, 15.0, "🦠", "#8B4513"),
    ("Мятая",          0.50, 15.0, "💥", "#B22222"),
    ("Царапанная",     0.65, 15.0, "⚡", "#A0522D"),
    ("Грязная",        0.75, 15.0, "💩", "#6B4423"),
    ("Граффити",       0.70, 10.0, "🎨", "#FF69B4"),
    ("Обычная",        1.00, 20.0, "🚗", "#94a3b8"),
    ("Ухоженная",      1.15,  5.0, "✨", "#22c55e"),
    ("Эксклюзивная",   1.40,  2.0, "🌟", "#a855f7"),
    ("Юбилейная №1",   2.00,  1.0, "🏆", "#fbbf24"),
    ("Коллекционная",  3.00,  0.5, "💎", "#22d3ee"),
]


def roll_modifier():
    weights = [m[2] for m in MODIFIERS]
    mod = random.choices(MODIFIERS, weights=weights, k=1)[0]
    return {
        "name": mod[0],
        "price_mult": mod[1],
        "emoji": mod[3],
        "color": mod[4],
    }


def modifier_meta(name):
    for m in MODIFIERS:
        if m[0] == name:
            return {"name": m[0], "price_mult": m[1], "emoji": m[3], "color": m[4]}
    return {"name": "Обычная", "price_mult": 1.0, "emoji": "🚗", "color": "#94a3b8"}


def calculate_price(brand, year, color, rarity, condition=100, country="germany"):
    country_data = COUNTRIES.get(country, COUNTRIES["germany"])
    base = country_data["brands"].get(brand, 3_000_000)

    age = 2025 - year
    year_mult = max(0.4, 1.0 - age * 0.02)
    if age > 30:
        year_mult += 0.5

    color_mult = COLORS.get(color, 1.0)
    rarity_mult = RARITY_MULT.get(rarity, 1.0)
    cond_mult = condition / 100

    return round(base * year_mult * color_mult * rarity_mult * cond_mult, 2)


def roll_car(country="germany", forced_rarity=None, apply_modifier=True):
    if forced_rarity:
        rarity = forced_rarity
    else:
        roll = random.random()
        if roll < 0.55:
            rarity = "common"
        elif roll < 0.85:
            rarity = "rare"
        elif roll < 0.97:
            rarity = "epic"
        else:
            rarity = "legendary"

    country_data = COUNTRIES.get(country, COUNTRIES["germany"])
    brand = random.choice(list(country_data["brands"].keys()))
    year = random.randint(1985, 2025)
    color = random.choices(
        list(COLORS.keys()),
        weights=[15, 12, 12, 10, 10, 5, 2, 3, 2, 1, 0.5, 0.3],
        k=1
    )[0]
    condition = random.randint(60, 100)

    price = calculate_price(brand, year, color, rarity, condition, country)

    result = {
        "brand": brand,
        "model": "",
        "year": year,
        "color": color,
        "rarity": rarity,
        "condition": condition,
        "price": price,
    }

    if apply_modifier:
        mod = roll_modifier()
        result["modifier"] = mod["name"]
        result["price"] = round(result["price"] * mod["price_mult"], 2)
    else:
        result["modifier"] = "Обычная"

    return result


def roll_car_from_case(country, case_price):
    """Возвращает машину из кейса. Цена = case_price * (0.5..1.6) * modifier."""
    country_data = COUNTRIES.get(country, COUNTRIES["germany"])
    brand = random.choice(list(country_data["brands"].keys()))
    year = random.randint(1985, 2025)

    # Определяем редкость по цене бренда относительно прайса кейса
    brand_base = country_data["brands"][brand]
    if brand_base >= case_price * 5:
        rarity = "legendary"
    elif brand_base >= case_price * 1.5:
        rarity = "epic"
    elif brand_base >= case_price * 0.4:
        rarity = "rare"
    else:
        rarity = "common"

    color = random.choices(
        list(COLORS.keys()),
        weights=[15, 12, 12, 10, 10, 5, 2, 3, 2, 1, 0.5, 0.3],
        k=1
    )[0]
    condition = random.randint(60, 100)

    # Базовая цена = цена кейса × случайный множитель
    base = case_price * random.uniform(0.5, 1.6)

    # Модификатор
    mod = roll_modifier()
    price = round(base * mod["price_mult"], 2)

    # Простая модель/название
    model = ""

    return {
        "brand": brand,
        "model": model,
        "year": year,
        "color": color,
        "rarity": rarity,
        "condition": condition,
        "modifier": mod["name"],
        "price": price,
    }
