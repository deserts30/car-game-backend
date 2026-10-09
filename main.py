import os
import asyncio
import random
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from game_logic import (
    roll_car, roll_car_from_case, modifier_meta, COUNTRIES, MODIFIERS,
)
from models import init_db, get_db, User, UserCar

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://deserts30.github.io/-rdrop/")

bot = None
dp = None

if BOT_TOKEN:
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(F.text == "/start")
    async def start(msg: Message):
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="🎮 Играть", web_app=WebAppInfo(url=WEBAPP_URL))
            ]]
        )
        await msg.answer(
            "🚗 Добро пожаловать в <b>Выбивание машин</b>!\n\n"
            "Крути рулетку, собирай коллекцию!",
            reply_markup=kb,
            parse_mode="HTML",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if BOT_TOKEN:
        asyncio.create_task(dp.start_polling(bot, handle_signals=False))
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ============ НАСТРОЙКИ ============
SPIN_COST = 500_000                 # Цена одной крутки
SPIN5_COST = 2_500_000              # Цена ×5 круток

BONUS_MONEY = 1_000_000             # Ежедневный бонус
WHEEL_COOLDOWN_MINUTES = 30         # Колесо удачи
TICKET_CASE_COST = 5                # Билетов на билетный кейс

XP_BY_RARITY = {
    "common": 10,
    "rare": 25,
    "epic": 60,
    "legendary": 150,
}

CONTAINERS = {
    "common":    {"name": "Обычный контейнер",     "price": 1_000_000},
    "rare":      {"name": "Редкий контейнер",      "price": 5_000_000},
    "epic":      {"name": "Эпический контейнер",   "price": 20_000_000},
    "legendary": {"name": "Легендарный контейнер", "price": 100_000_000},
    "elite":     {"name": "Элитный контейнер",     "price": 500_000_000},
}

# Элитный кейс имеет шанс выдать эксклюзив
ELITE_SPECIAL_CHANCE = 0.01
SPECIALS = [
    ("Bugatti", "Cristiano Ronaldo", 10_000_000_000, "legendary", "Юбилейная", "Юбилейная №1"),
    ("Rolls-Royce", "Sheikh Edition", 3_500_000_000, "legendary", "Золотой", "Эксклюзивная"),
    ("Ferrari", "LaFerrari Aperta", 2_500_000_000, "legendary", "Красный", "Коллекционная"),
]


def xp_for_next_level(level: int) -> int:
    return 100 * level * level


def add_xp(user: User, amount: int):
    user.xp += amount
    while user.xp >= xp_for_next_level(user.level):
        user.xp -= xp_for_next_level(user.level)
        user.level += 1


class InitData(BaseModel):
    tg_id: int
    username: str = "player"


class CountryData(BaseModel):
    country: str


def car_to_dict(c: UserCar):
    return {
        "id": c.id,
        "brand": c.brand,
        "model": c.model,
        "year": c.year,
        "color": c.color,
        "rarity": c.rarity,
        "modifier": c.modifier or "Обычная",
        "modifier_meta": modifier_meta(c.modifier or "Обычная"),
        "condition": c.condition,
        "price": c.price,
    }


def user_to_dict(u: User):
    return {
        "balance": u.balance,
        "tickets": u.tickets,
        "level": u.level,
        "xp": u.xp,
        "xp_next": xp_for_next_level(u.level),
        "total_cars_obtained": u.total_cars_obtained,
        "country": u.country,
        "cars": [car_to_dict(c) for c in u.cars],
    }


def make_car(user, car_data):
    return UserCar(
        user_id=user.id,
        brand=car_data["brand"],
        model=car_data.get("model", ""),
        year=car_data["year"],
        color=car_data["color"],
        rarity=car_data["rarity"],
        modifier=car_data.get("modifier", "Обычная"),
        condition=car_data.get("condition", 100),
        price=car_data["price"],
    )


# ============ ЭНДПОИНТЫ ============

@app.get("/")
def root():
    return {"message": "Car Game API v2"}


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}


@app.get("/api/config")
def get_config():
    return {
        "spin_cost": SPIN_COST,
        "spin5_cost": SPIN5_COST,
        "bonus_money": BONUS_MONEY,
        "wheel_cooldown_minutes": WHEEL_COOLDOWN_MINUTES,
        "ticket_case_cost": TICKET_CASE_COST,
        "containers": [
            {"id": k, "name": v["name"], "price": v["price"]}
            for k, v in CONTAINERS.items()
        ],
    }


@app.get("/api/countries")
def get_countries():
    return {k: v["name"] for k, v in COUNTRIES.items()}


@app.get("/api/modifiers")
def get_modifiers():
    return [
        {"name": m[0], "mult": m[1], "emoji": m[3], "color": m[4]}
        for m in MODIFIERS
    ]


@app.get("/api/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).all()
    rows = []
    for u in users:
        garage_value = sum(c.price for c in u.cars)
        rows.append({
            "tg_id": u.tg_id,
            "username": u.username or "Игрок",
            "level": u.level,
            "cars_count": len(u.cars),
            "garage_value": round(garage_value, 2),
        })
    rows.sort(key=lambda x: x["garage_value"], reverse=True)
    return {"leaders": rows[:50], "total": len(rows)}


@app.post("/api/country/{tg_id}")
def set_country(tg_id: int, data: CountryData, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if data.country not in COUNTRIES:
        raise HTTPException(400, "Unknown country")
    user.country = data.country
    db.commit()
    return {"country": user.country}


@app.post("/api/auth")
def auth(data: InitData, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == data.tg_id).first()
    if not user:
        user = User(tg_id=data.tg_id, username=data.username)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if data.username and user.username != data.username:
            user.username = data.username
            db.commit()
    return user_to_dict(user)


@app.post("/api/roll/{tg_id}")
def do_roll(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if user.balance < SPIN_COST:
        raise HTTPException(400, f"Нужно {SPIN_COST:,} ₽")

    user.balance -= SPIN_COST
    car_data = roll_car(country=user.country)

    xp_gained = XP_BY_RARITY.get(car_data["rarity"], 10)
    add_xp(user, xp_gained)
    user.total_cars_obtained += 1

    car = make_car(user, car_data)
    db.add(car)
    db.commit()
    db.refresh(user)
    db.refresh(car)

    return {
        "car": car_to_dict(car),
        "balance": user.balance,
        "level": user.level,
        "xp": user.xp,
        "xp_next": xp_for_next_level(user.level),
        "xp_gained": xp_gained,
    }


@app.post("/api/roll5/{tg_id}")
def do_roll5(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if user.balance < SPIN5_COST:
        raise HTTPException(400, f"Нужно {SPIN5_COST:,} ₽")

    user.balance -= SPIN5_COST
    total_xp = 0
    cars_objs = []

    for _ in range(5):
        car_data = roll_car(country=user.country)
        xp_gained = XP_BY_RARITY.get(car_data["rarity"], 10)
        add_xp(user, xp_gained)
        total_xp += xp_gained
        user.total_cars_obtained += 1
        car = make_car(user, car_data)
        db.add(car)
        cars_objs.append(car)

    db.commit()
    db.refresh(user)
    for c in cars_objs:
        db.refresh(c)

    return {
        "cars": [car_to_dict(c) for c in cars_objs],
        "balance": user.balance,
        "level": user.level,
        "xp": user.xp,
        "xp_next": xp_for_next_level(user.level),
        "xp_gained": total_xp,
    }


@app.post("/api/container/{tg_id}/{container_type}")
def open_container(tg_id: int, container_type: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if container_type not in CONTAINERS:
        raise HTTPException(400, "Unknown container")

    cont = CONTAINERS[container_type]
    if user.balance < cont["price"]:
        raise HTTPException(400, f"Нужно {cont['price']:,} ₽")

    user.balance -= cont["price"]

    # Элитный кейс — шанс на эксклюзив
    is_special = False
    if container_type == "elite" and random.random() < ELITE_SPECIAL_CHANCE:
        special = random.choice(SPECIALS)
        car_data = {
            "brand": special[0],
            "model": special[1],
            "year": 2024,
            "color": special[4],
            "rarity": special[3],
            "modifier": special[5],
            "condition": 100,
            "price": special[2],
        }
        is_special = True
    else:
        car_data = roll_car_from_case(user.country, cont["price"])

    xp_gained = XP_BY_RARITY.get(car_data["rarity"], 10)
    add_xp(user, xp_gained)
    user.total_cars_obtained += 1

    car = make_car(user, car_data)
    db.add(car)
    db.commit()
    db.refresh(user)
    db.refresh(car)

    return {
        "car": car_to_dict(car),
        "balance": user.balance,
        "level": user.level,
        "xp": user.xp,
        "xp_next": xp_for_next_level(user.level),
        "xp_gained": xp_gained,
        "is_special": is_special,
    }


# ============ КОЛЕСО УДАЧИ ============
WHEEL_PRIZES = [
    ("money", 500_000, 30),
    ("money", 1_000_000, 25),
    ("money", 3_000_000, 15),
    ("money", 10_000_000, 5),
    ("tickets", 1, 12),
    ("tickets", 3, 5),
    ("case", "common", 6),
    ("case", "rare", 2),
]


def wheel_prize_dict(prize):
    kind, value, _ = prize
    if kind == "money":
        return {"type": "money", "value": value, "label": f"{value:,} ₽", "emoji": "💰"}
    if kind == "tickets":
        return {"type": "tickets", "value": value, "label": f"{value} 🎫", "emoji": "🎫"}
    if kind == "case":
        return {"type": "case", "value": value, "label": f"{CONTAINERS[value]['name']}", "emoji": "📦"}
    return {"type": "unknown", "value": 0, "label": "?", "emoji": "❓"}


@app.get("/api/wheel/{tg_id}")
def get_wheel_state(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    now = datetime.utcnow()
    available = True
    remaining = 0
    if user.last_wheel:
        delta = (now - user.last_wheel).total_seconds()
        total = WHEEL_COOLDOWN_MINUTES * 60
        if delta < total:
            available = False
            remaining = int(total - delta)
    return {"available": available, "remaining_seconds": remaining}


@app.post("/api/wheel/{tg_id}")
def spin_wheel(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    now = datetime.utcnow()
    if user.last_wheel:
        delta = (now - user.last_wheel).total_seconds()
        total = WHEEL_COOLDOWN_MINUTES * 60
        if delta < total:
            remaining = int(total - delta)
            m = remaining // 60
            s = remaining % 60
            raise HTTPException(400, f"Колесо будет доступно через {m} мин {s} сек")

    weights = [p[2] for p in WHEEL_PRIZES]
    prize = random.choices(WHEEL_PRIZES, weights=weights, k=1)[0]
    kind, value, _ = prize

    result_text = ""
    if kind == "money":
        user.balance += value
        result_text = f"+{value:,} ₽"
    elif kind == "tickets":
        user.tickets += value
        result_text = f"+{value} 🎫"
    elif kind == "case":
        car_data = roll_car_from_case(user.country, CONTAINERS[value]["price"])
        car = make_car(user, car_data)
        db.add(car)
        result_text = f"Машина: {car_data['brand']}"

    user.last_wheel = now
    db.commit()
    db.refresh(user)

    return {
        "prize": wheel_prize_dict(prize),
        "result_text": result_text,
        "balance": user.balance,
        "tickets": user.tickets,
    }


# ============ БИЛЕТНЫЙ КЕЙС ============
TICKET_CASE_REWARDS = [
    ("money", 500_000, 20),
    ("money", 2_000_000, 15),
    ("money", 5_000_000, 8),
    ("tickets", 1, 10),
    ("xp", 200, 15),
    ("xp", 1000, 7),
    ("car", None, 25),
]


@app.post("/api/ticket-case/{tg_id}")
def open_ticket_case(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if user.tickets < TICKET_CASE_COST:
        raise HTTPException(400, f"Нужно {TICKET_CASE_COST} 🎫")

    user.tickets -= TICKET_CASE_COST

    weights = [r[2] for r in TICKET_CASE_REWARDS]
    reward = random.choices(TICKET_CASE_REWARDS, weights=weights, k=1)[0]
    kind, value, _ = reward

    result = {}
    if kind == "money":
        user.balance += value
        result = {"type": "money", "value": value, "label": f"+{value:,} ₽"}
    elif kind == "tickets":
        user.tickets += value
        result = {"type": "tickets", "value": value, "label": f"+{value} 🎫"}
    elif kind == "xp":
        add_xp(user, value)
        result = {"type": "xp", "value": value, "label": f"+{value} XP"}
    elif kind == "car":
        # Дешёвая машина из билетного кейса
        car_data = roll_car_from_case(user.country, 2_000_000)
        car = make_car(user, car_data)
        db.add(car)
        user.total_cars_obtained += 1
        result = {
            "type": "car",
            "car": car_to_dict(car) if hasattr(car, 'id') else car_data,
        }
        db.flush()
        result["car"] = car_to_dict(car)

    db.commit()
    db.refresh(user)

    return {
        "reward": result,
        "balance": user.balance,
        "tickets": user.tickets,
        "level": user.level,
        "xp": user.xp,
        "xp_next": xp_for_next_level(user.level),
    }


# ============ ГАРАЖ, ПРОДАЖА, БОНУС ============

@app.get("/api/garage/{tg_id}")
def garage(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        return {"cars": []}
    return {"cars": [car_to_dict(c) for c in user.cars]}


@app.post("/api/sell/{tg_id}/{car_id}")
def sell_car(tg_id: int, car_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    car = db.query(UserCar).filter(UserCar.id == car_id, UserCar.user_id == user.id).first()
    if not car:
        raise HTTPException(404, "Car not found")
    sell_price = round(car.price * 0.7, 2)
    user.balance += sell_price
    db.delete(car)
    db.commit()
    db.refresh(user)
    return {"sold_price": sell_price, "new_balance": user.balance}


@app.post("/api/sell-all/{tg_id}")
def sell_all(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    cars = db.query(UserCar).filter(UserCar.user_id == user.id).all()
    if not cars:
        raise HTTPException(400, "Гараж пуст")
    total = round(sum(c.price * 0.7 for c in cars), 2)
    count = len(cars)
    for c in cars:
        db.delete(c)
    user.balance += total
    db.commit()
    db.refresh(user)
    return {"sold_count": count, "sold_total": total, "new_balance": user.balance}


@app.post("/api/bonus/{tg_id}")
def claim_bonus(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    now = datetime.utcnow()
    if user.last_bonus:
        delta = now - user.last_bonus
        if delta.total_seconds() < 24 * 3600:
            remaining = 24 * 3600 - delta.total_seconds()
            h = int(remaining // 3600)
            m = int((remaining % 3600) // 60)
            raise HTTPException(400, f"Бонус доступен через {h} ч {m} мин")

    user.balance += BONUS_MONEY
    user.last_bonus = now
    db.commit()
    db.refresh(user)

    return {
        "bonus_money": BONUS_MONEY,
        "new_balance": user.balance,
    }
