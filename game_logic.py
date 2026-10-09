import random

COLORS = {
    "Чёрный": 1.0, "Белый": 1.05, "Серебристый": 1.1,
    "Красный": 1.15, "Синий": 1.12, "Жёлтый": 1.3,
    "Хамелеон": 1.8, "Матовый чёрный": 1.5,
    "Розовый": 1.6, "Золотой": 2.2, "Радужный": 2.8, "Юбилейная": 3.0,
}

# ============ КАТАЛОГ МАШИН ============
# (brand, model, year, base_price)
CAR_CATALOG = [
    # Lada
    ("Lada", "2101", 1972, 427500),
    ("Lada", "2101", 1978, 475000),
    ("Lada", "2101", 1985, 265050),
    ("Lada", "2101", 1990, 522500),
    ("Lada", "2101", 1980, 807500),
    ("Lada", "21011", 1975, 209000),
    ("Lada", "2101", 1978, 142500),
    ("Lada", "2112", 2000, 147250),
    ("Lada", "2101", 1975, 57000),
    ("Lada", "2101", 1995, 52500),
    ("Lada", "2101 б/д", 1990, 37050),
    # BMW
    ("BMW", "318i", 2007, 418000),
    ("BMW", "318D", 2015, 945250),
    ("BMW", "118i", 2009, 370500),
    ("BMW", "535", 2015, 950000),
    ("BMW", "X1", 2016, 1139050),
    ("BMW", "X3 2.0D", 2019, 1947500),
    ("BMW", "X6 3.5d", 2010, 983250),
    ("BMW", "320i e46", 1998, 142500),
    ("BMW", "M4 Competition", 2024, 7314050),
    ("BMW", "840 M Sport", 2022, 5129050),
    # Audi
    ("Audi", "A6 3.0 TDI", 2007, 236550),
    ("Audi", "A6 C7 3.0 TDI", 2015, 760000),
    ("Audi", "A6 2.7 TDI", 2007, 313500),
    ("Audi", "A6 3.0 TDI", 2013, 1045000),
    ("Audi", "A6 3.0 TDI C6", 2005, 123500),
    ("Audi", "Q5 Hybrid", 2024, 3211000),
    ("Audi", "RS3", 2024, 5082500),
    # Mercedes
    ("Mercedes", "ML 55 AMG", 2000, 304000),
    ("Mercedes", "280", 1977, 1691000),
    ("Mercedes", "250", 2010, 565250),
    # Renault
    ("Renault", "Clio Grandtour", 2014, 427500),
    ("Renault", "Captur", 2016, 807500),
    ("Renault", "Clio", 2014, 521550),
    ("Renault", "Megane", 2009, 375250),
    ("Renault", "Megane", 2008, 256500),
    ("Renault", "Megane 1.9dCi", 2007, 246050),
    ("Renault", "Megane Estate", 2022, 1139050),
    ("Renault", "Master L3H2", 2020, 1596000),
    ("Renault", "Master Panel", 2018, 1320500),
    # Volvo
    ("Volvo", "XC60", 2012, 470250),
    ("Volvo", "V60 Cross Country", 2016, 845500),
    ("Volvo", "XC60 CC", 2023, 3401000),
    ("Volvo", "XC90 Inscription", 2023, 4370000),
    # Volkswagen
    ("Volkswagen", "Passat B7", 2011, 414950),
    ("Volkswagen", "B7", 2011, 342000),
    ("Volkswagen", "Golf 5", 2006, 190000),
    ("Volkswagen", "Golf 7", 2013, 560500),
    ("Volkswagen", "Tiguan", 2009, 603250),
    ("Volkswagen", "Sharan", 2005, 389500),
    ("Volkswagen", "Passat B8", 2015, 1187500),
    ("Volkswagen", "ID3 Pro", 2020, 1899050),
    ("Volkswagen", "ID4 Pro", 2021, 2469050),
    ("Volkswagen", "T-Roc", 2026, 2736000),
    # Toyota
    ("Toyota", "Auris", 2014, 622250),
    ("Toyota", "Corolla TS", 2019, 1558000),
    ("Toyota", "Hilux", 2025, 4835500),
    ("Toyota", "Verso", 2013, 375250),
    ("Toyota", "Land Cruiser 120", 2010, 807500),
    ("Toyota", "Yaris", 2012, 361000),
    ("Toyota", "Aygo", 2010, 275500),
    # Ford
    ("Ford", "C-Max", 2017, 1891450),
    ("Ford", "Connect", 2017, 1695750),
    ("Ford", "Focus RS", 2018, 3592900),
    ("Ford", "Kuga Titanium", 2018, 3120750),
    ("Ford", "Mustang GT", 2018, 4045100),
    ("Ford", "Mondeo Trend", 2018, 2259050),
    ("Ford", "Transit Van", 2018, 2597300),
    # Mazda
    ("Mazda", "Mazda6", 2010, 380475),
    ("Mazda", "Mazda3", 2010, 393490),
    ("Mazda", "CX-5", 2015, 900600),
    ("Mazda", "CX-7", 2010, 399950),
    ("Mazda", "CX-7 2.0", 2008, 228000),
    ("Mazda", "Mazda5", 2007, 236740),
    ("Mazda", "Mazda2", 2010, 116185),
    # Mitsubishi
    ("Mitsubishi", "Colt Cz3", 2006, 90250),
    ("Mitsubishi", "Colt 1.5D", 2006, 152000),
    ("Mitsubishi", "Eclipse GT", 2000, 190000),
    ("Mitsubishi", "купе 1.3", 1995, 46550),
    ("Mitsubishi", "купе 2.0", 1998, 95000),
    ("Mitsubishi", "купе", 2005, 693500),
    ("Mitsubishi", "купе 2.4", 2002, 351500),
    # Škoda
    ("Škoda", "Fabia", 2022, 1230250),
    # Ferrari
    ("Ferrari", "458 Italia", 2015, 17005000),
    ("Ferrari", "Italia", 2018, 12840200),
    # Honda
    ("Honda", "CR-V 1.6D", 2017, 1186550),
    ("Honda", "CR-V AWD", 2015, 1092500),
    ("Honda", "CR-V", 2010, 749550),
    ("Honda", "Civic 2.2D", 2007, 351500),
    # Chevrolet
    ("Chevrolet", "Spark 1.0", 2010, 218500),
    # Hyundai
    ("Hyundai", "ix35 2.0D", 2011, 522500),
    ("Hyundai", "ix35 2.0", 2011, 688750),
    ("Hyundai", "ix35 CRDi", 2011, 802750),
    # Nissan
    ("Nissan", "Micra", 2023, 1424050),
    # Opel
    ("Opel", "Insignia 2.0", 2015, 664050),
    ("Opel", "Mokka X", 2018, 854050),
    ("Opel", "Frontera", 2024, 2555500),
    ("Opel", "1.7D", 2005, 42750),
    ("Opel", "1.4", 2005, 42750),
    # Peugeot
    ("Peugeot", "2008 1.5D", 2020, 1353750),
    ("Peugeot", "2008 GT Line", 2022, 1881000),
    ("Peugeot", "2008 1.2", 2020, 1353750),
]

# Разбиваем каталог на тиры
TIER_LOW     = [c for c in CAR_CATALOG if c[3] < 250_000]
TIER_MIDLOW  = [c for c in CAR_CATALOG if 200_000 <= c[3] < 650_000]
TIER_MID     = [c for c in CAR_CATALOG if 500_000 <= c[3] < 1_800_000]
TIER_HIGH    = [c for c in CAR_CATALOG if 1_500_000 <= c[3] < 5_000_000]
TIER_TOP     = [c for c in CAR_CATALOG if c[3] >= 5_000_000]


RARITY_BY_PRICE = [
    (150_000, "common"),
    (700_000, "rare"),
    (3_000_000, "epic"),
    (999_999_999_999, "legendary"),
]

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

# ============ АПГРЕЙДЫ ============
# Парты машины
UPGRADE_PARTS = ["kuzov", "podveska", "dvigatel", "turbina"]

# Множители по уровню парта (0-4)
PART_MULTS = [1, 2, 3, 5, 10]

# Шансы успеха при переходе на след. уровень
UPGRADE_CHANCES = [40, 27, 16, 8]  # на 1→2, 2→3, 3→5, 4→10

# Цена попытки (% от base_price машины)
UPGRADE_COST_PCT = [0.15, 0.30, 0.55, 0.90]


def roll_modifier():
    weights = [m[2] for m in MODIFIERS]
    mod = random.choices(MODIFIERS, weights=weights, k=1)[0]
    return {"name": mod[0], "price_mult": mod[1], "emoji": mod[3], "color": mod[4]}


def modifier_meta(name):
    for m in MODIFIERS:
        if m[0] == name:
            return {"name": m[0], "price_mult": m[1], "emoji": m[3], "color": m[4]}
    return {"name": "Обычная", "price_mult": 1.0, "emoji": "🚗", "color": "#94a3b8"}


def rarity_from_price(price):
    for cap, r in RARITY_BY_PRICE:
        if price < cap:
            return r
    return "legendary"


def pick_car_from_tier(tier_list):
    """Берёт случайную машину из тира и применяет модификатор."""
    brand, model, year, base = random.choice(tier_list)
    color = random.choices(
        list(COLORS.keys()),
        weights=[15, 12, 12, 10, 10, 5, 2, 3, 2, 1, 0.5, 0.3], k=1
    )[0]
    condition = random.randint(60, 100)
    mod = roll_modifier()
    price = round(base * mod["price_mult"] * random.uniform(0.85, 1.2), 2)
    return {
        "brand": brand,
        "model": model,
        "year": year,
        "color": color,
        "rarity": rarity_from_price(base),
        "condition": condition,
        "modifier": mod["name"],
        "price": price,
        "base_price": base,
    }


def roll_spin_car():
    """Обычная крутка — из тира MIDLOW/MID (цена ~30к-1.5M)."""
    tier = random.choices([TIER_MIDLOW, TIER_MID], weights=[70, 30], k=1)[0]
    return pick_car_from_tier(tier)


def roll_case_car(case_id):
    """Машина из кейса."""
    if case_id == "case50":
        return pick_car_from_tier(TIER_LOW)
    if case_id == "case250":
        tier = random.choices([TIER_LOW, TIER_MIDLOW], weights=[30, 70], k=1)[0]
        return pick_car_from_tier(tier)
    if case_id == "case500":
        tier = random.choices([TIER_MIDLOW, TIER_MID], weights=[50, 50], k=1)[0]
        return pick_car_from_tier(tier)
    if case_id == "case1m":
        tier = random.choices([TIER_MID, TIER_HIGH, TIER_TOP], weights=[50, 40, 10], k=1)[0]
        return pick_car_from_tier(tier)
    return pick_car_from_tier(TIER_MIDLOW)
