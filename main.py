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
    roll_car, roll_modifier, modifier_meta, COUNTRIES,
    SPECIAL_CARS, MODIFIERS,
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
                InlineKeyboardButton(
                    text="🎮 Играть",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]]
        )
        await msg.answer(
            "🚗 Добро пожаловать в <b>Выбивание машин</b>!\n\n"
            "Выбивай тачки, собирай коллекцию!",
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


ENERGY_RESTORE_MINUTES = 5

XP_BY_RARITY = {
    "common": 10,
    "rare": 25,
    "epic": 60,
    "legendary": 150,
}

CONTAINERS = {
    "common": {
        "name": "Обычный контейнер",
        "price": 10000,
        "weights": {"common": 82, "rare": 15, "epic": 2.7, "legendary": 0.3},
    },
    "rare": {
        "name": "Редкий контейнер",
        "price": 30000,
        "weights": {"common": 50, "rare": 38, "epic": 10, "legendary": 2},
    },
    "epic": {
        "name": "Эпический контейнер",
        "price": 100000,
        "weights": {"common": 15, "rare": 45, "epic": 35, "legendary": 5},
    },
    "legendary": {
        "name": "Легендарный контейнер",
        "price": 300000,
        "weights": {"rare": 25, "epic": 55, "legendary": 20},
    },
    "elite": {
        "name": "Элитный контейнер",
        "price": 1000000,
        "weights": {"epic": 35, "legendary": 65},
    },
}

# Масштаб цены автомобиля внутри кейса
CASE_BASE_SCALE = {
    "common": 0.005,
    "rare": 0.012,
    "epic": 0.030,
    "legendary": 0.080,
    "elite": 0.150,
}

# Максимальная цена машины из кейса (не даёт сломать экономику)
CASE_MAX_PRICE = {
    "common": 200000,
    "rare": 500000,
    "epic": 2000000,
    "legendary": 5000000,
    "elite": 15000000,
}


def xp_for_next_level(level: int) -> int:
    return 100 * level * level


def add_xp(user: User, amount: int):
    user.xp += amount
    while user.xp >= xp_for_next_level(user.level):
        user.xp -= xp_for_next_level(user.level)
        user.level += 1


def restore_energy(user: User, db: Session):
    now = datetime.utcnow()
    if user.last_energy_update is None:
        user.last_energy_update = now
        db.commit()
        return
    if user.energy >= user.max_energy:
        user.last_energy_update = now
        db.commit()
        return
    elapsed = (now - user.last_energy_update).total_seconds()
    energy_to_add = int(elapsed // (ENERGY_RESTORE_MINUTES * 60))
    if energy_to_add > 0:
        user.energy = min(user.energy + energy_to_add, user.max_energy)
        user.last_energy_update = user.last_energy_update + timedelta(
            minutes=energy_to_add * ENERGY_RESTORE_MINUTES
        )
        if user.energy >= user.max_energy:
            user.last_energy_update = now
        db.commit()


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
        "energy": u.energy,
        "max_energy": u.max_energy,
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


@app.get("/")
def root():
    return {"message": "Car Game API + Bot running"}


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}


@app.get("/api/countries")
def get_countries():
    return {k: v["name"] for k, v in COUNTRIES.items()}


@app.get("/api/modifiers")
def get_modifiers():
    return [
        {
            "name": m[0],
            "mult": m[1],
            "emoji": m[3],
            "color": m[4],
            "weight": m[2],
        }
        for m in MODIFIERS
    ]


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
    restore_energy(user, db)
    db.refresh(user)
    return user_to_dict(user)


@app.post("/api/roll/{tg_id}")
def do_roll(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    restore_energy(user, db)
    db.refresh(user)

    if user.energy <= 0:
        raise HTTPException(400, "Нет энергии")

    user.energy -= 1
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
        "energy": user.energy,
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

    restore_energy(user, db)
    db.refresh(user)

    if user.energy < 5:
        raise HTTPException(400, "Нужно 5 энергии")

    user.energy -= 5
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
        "energy": user.energy,
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
        raise HTTPException(400, f"Нужно {cont['price']} ₽")

    user.balance -= cont["price"]

    # --- 1. Проверка на эксклюзивную именованную машину ---
    special = None
    for sc in SPECIAL_CARS:
        if container_type in sc["only_in"]:
            if random.random() < sc["chance"]:
                special = sc
                break

    if special:
        car_data = {
            "brand": special["brand"],
            "model": special["model"],
            "year": 2024,
            "color": special["color"],
            "rarity": special["rarity"],
            "modifier": special["modifier"],
            "condition": 100,
            "price": special["base_price"],
        }
    else:
        # --- 2. Обычная машина с модификатором ---
        rarities = list(cont["weights"].keys())
        weights = list(cont["weights"].values())
        rarity = random.choices(rarities, weights=weights, k=1)[0]

        car_data = roll_car(
            country=user.country,
            forced_rarity=rarity,
            apply_modifier=True,
        )

        # Масштабируем цену под уровень кейса
        car_data["price"] = round(
            car_data["price"] * CASE_BASE_SCALE[container_type], 2
        )

        # Кэп по максимуму для этого кейса
        car_data["price"] = min(car_data["price"], CASE_MAX_PRICE[container_type])

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
        "energy": user.energy,
        "balance": user.balance,
        "level": user.level,
        "xp": user.xp,
        "xp_next": xp_for_next_level(user.level),
        "xp_gained": xp_gained,
        "is_special": special is not None,
    }


@app.get("/api/garage/{tg_id}")
def garage(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        return {"cars": []}

    restore_energy(user, db)
    db.refresh(user)

    return {"cars": [car_to_dict(c) for c in user.cars]}


@app.post("/api/sell/{tg_id}/{car_id}")
def sell_car(tg_id: int, car_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    car = db.query(UserCar).filter(
        UserCar.id == car_id,
        UserCar.user_id == user.id
    ).first()
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

    return {
        "sold_count": count,
        "sold_total": total,
        "new_balance": user.balance,
    }


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
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            raise HTTPException(400, f"Бонус будет доступен через {hours} ч {minutes} мин")

    bonus_money = 500
    bonus_energy = 5

    user.balance += bonus_money
    user.energy = min(user.energy + bonus_energy, user.max_energy)
    user.last_bonus = now
    db.commit()
    db.refresh(user)

    return {
        "bonus_money": bonus_money,
        "bonus_energy": bonus_energy,
        "new_balance": user.balance,
        "new_energy": user.energy,
    }
