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
}

COUNTRIES = {
    "russia": {
        "name": "🇷🇺 Россия",
        "brands": {
            "Lada": 20000,
            "GAZ": 25000,
            "UAZ": 28000,
            "Moskvich": 15000,
            "ZIL": 30000,
            "KAMAZ": 40000,
        },
    },
    "germany": {
        "name": "🇩🇪 Германия",
        "brands": {
            "BMW": 80000,
            "Mercedes": 85000,
            "Audi": 75000,
            "Porsche": 200000,
            "Volkswagen": 45000,
            "Opel": 35000,
        },
    },
    "italy": {
        "name": "🇮🇹 Италия",
        "brands": {
            "Ferrari": 500000,
            "Lamborghini": 450000,
            "Maserati": 250000,
            "Alfa Romeo": 90000,
            "Fiat": 25000,
        },
    },
    "usa": {
        "name": "🇺🇸 США",
        "brands": {
            "Ford": 60000,
            "Chevrolet": 65000,
            "Tesla": 150000,
            "Dodge": 90000,
            "Cadillac": 120000,
            "Jeep": 70000,
        },
    },
    "japan": {
        "name": "🇯🇵 Япония",
        "brands": {
            "Toyota": 50000,
            "Honda": 45000,
            "Nissan": 48000,
            "Mazda": 42000,
            "Subaru": 55000,
            "Lexus": 110000,
        },
    },
    "dubai": {
        "name": "🇦🇪 Дубай",
        "brands": {
            "Bugatti": 2000000,
            "Koenigsegg": 1800000,
            "Rolls-Royce": 800000,
            "Bentley": 500000,
            "McLaren": 600000,
            "Maybach": 400000,
        },
    },
}

RARITY_MULT = {
    "common": 1.0,
    "rare": 1.5,
    "epic": 2.5,
    "legendary": 5.0,
}

# ==== МОДИФИКАТОРЫ СОСТОЯНИЯ ====
# (название, множитель цены, вес, эмодзи, цвет)
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

# ==== ЭКСКЛЮЗИВНЫЕ ИМЕНОВАННЫЕ МАШИНЫ ====
SPECIAL_CARS = [
    {
        "brand": "Bugatti",
        "model": "Cristiano Ronaldo",
        "base_price": 10000000,
        "rarity": "legendary",
        "color": "Юбилейная",
        "modifier": "Юбилейная №1",
        "only_in": ["elite"],
        "chance": 0.003,   # 0.3% в элитном кейсе
    },
    {
        "brand": "Rolls-Royce",
        "model": "Sheikh Edition",
        "base_price": 3500000,
        "rarity": "legendary",
        "color": "Золотой",
        "modifier": "Эксклюзивная",
        "only_in": ["legendary", "elite"],
        "chance": 0.008,
    },
    {
        "brand": "Ferrari",
        "model": "LaFerrari Aperta",
        "base_price": 2500000,
        "rarity": "legendary",
        "color": "Красный",
        "modifier": "Коллекционная",
        "only_in": ["epic", "legendary", "elite"],
        "chance": 0.006,
    },
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
    base = country_data["brands"].get(brand, 30000)

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
        weights=[15, 12, 12, 10, 10, 5, 2, 3, 2, 1, 0.5],
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
