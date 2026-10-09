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
        },
    },
}

RARITY_MULT = {
    "common": 1.0,
    "rare": 1.5,
    "epic": 2.5,
    "legendary": 5.0,
}


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


def roll_car(country="germany", forced_rarity=None):
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
        weights=[15, 12, 12, 10, 10, 5, 2, 3],
        k=1
    )[0]
    condition = random.randint(60, 100)

    price = calculate_price(brand, year, color, rarity, condition, country)

    return {
        "brand": brand,
        "model": "",
        "year": year,
        "color": color,
        "rarity": rarity,
        "condition": condition,
        "price": price,
    }
