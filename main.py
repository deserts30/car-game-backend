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
    roll_spin_car, roll_case_car, modifier_meta,
    PART_MULTS, UPGRADE_CHANCES, UPGRADE_COST_PCT, UPGRADE_PARTS,
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
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🎮 Играть", web_app=WebAppInfo(url=WEBAPP_URL))
        ]])
        await msg.answer(
            "🚗 Добро пожаловать в <b>Выбивание машин</b>!\n\nКрути, собирай, апгрейди!",
            reply_markup=kb, parse_mode="HTML",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if BOT_TOKEN:
        asyncio.create_task(dp.start_polling(bot, handle_signals=False))
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SPIN_COST = 30_000
SPIN5_COST = 120_000
BONUS_MONEY = 100_000
WHEEL_COOLDOWN_MINUTES = 30
TICKET_CASE_COST = 5

XP_BY_RARITY = {"common": 10, "rare": 25, "epic": 60, "legendary": 150}

CASES = {
    "case50":  {"name": "Обычный кейс",      "price": 50_000},
    "case250": {"name": "Редкий кейс",       "price": 250_000},
    "case500": {"name": "Эпический кейс",    "price": 500_000},
    "case1m":  {"name": "Легендарный кейс",  "price": 1_000_000},
}

WHEEL_PRIZES = [
    ("money", 30_000, 25),
    ("money", 60_000, 25),
    ("money", 120_000, 20),
    ("money", 400_000, 10),
    ("tickets", 1, 12),
    ("tickets", 3, 5),
    ("case", "case50", 2),
    ("case", "case250", 1),
]


def xp_for_next_level(level: int) -> int:
    return 100 * level * level


def add_xp(user: User, amount: int):
    user.xp += amount
    while user.xp >= xp_for_next_level(user.level):
        user.xp -= xp_for_next_level(user.level)
        user.level += 1


def car_multiplier(c: UserCar):
    total = (
        PART_MULTS[c.kuzov_lvl or 0]
        + PART_MULTS[c.podveska_lvl or 0]
        + PART_MULTS[c.dvigatel_lvl or 0]
        + PART_MULTS[c.turbina_lvl or 0]
    )
    return total / 4.0


def recalc_price(c: UserCar):
    c.price = round(c.base_price * car_multiplier(c), 2)


def car_to_dict(c: UserCar):
    mult = car_multiplier(c)
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
        "base_price": c.base_price,
        "price": c.price,
        "multiplier": round(mult, 2),
        "kuzov_lvl": c.kuzov_lvl or 0,
        "podveska_lvl": c.podveska_lvl or 0,
        "dvigatel_lvl": c.dvigatel_lvl or 0,
        "turbina_lvl": c.turbina_lvl or 0,
    }


def user_to_dict(u: User):
    return {
        "balance": u.balance,
        "tickets": u.tickets,
        "level": u.level,
        "xp": u.xp,
        "xp_next": xp_for_next_level(u.level),
        "total_cars_obtained": u.total_cars_obtained,
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
        base_price=car_data.get("base_price", car_data["price"]),
        price=car_data["price"],
    )


class InitData(BaseModel):
    tg_id: int
    username: str = "player"


@app.get("/")
def root():
    return {"message": "Car Game API v3"}


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
        "cases": [{"id": k, "name": v["name"], "price": v["price"]} for k, v in CASES.items()],
        "upgrade_parts": UPGRADE_PARTS,
        "part_mults": PART_MULTS,
        "upgrade_chances": UPGRADE_CHANCES,
        "upgrade_cost_pct": UPGRADE_COST_PCT,
    }


@app.get("/api/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).all()
    rows = []
    for u in users:
        garage_val = sum(c.price for c in u.cars)
        rows.append({
            "tg_id": u.tg_id,
            "username": u.username or "Игрок",
            "level": u.level,
            "cars_count": len(u.cars),
            "garage_value": round(garage_val, 2),
        })
    rows.sort(key=lambda x: x["garage_value"], reverse=True)
    return {"leaders": rows[:50], "total": len(rows)}


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
    car_data = roll_spin_car()
    xp_g = XP_BY_RARITY.get(car_data["rarity"], 10)
    add_xp(user, xp_g)
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
        "xp_gained": xp_g,
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
        car_data = roll_spin_car()
        xp_g = XP_BY_RARITY.get(car_data["rarity"], 10)
        add_xp(user, xp_g)
        total_xp += xp_g
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


@app.post("/api/case/{tg_id}/{case_id}")
def open_case(tg_id: int, case_id: str, count: int = 1, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if case_id not in CASES:
        raise HTTPException(400, "Unknown case")
    if count < 1 or count > 5:
        raise HTTPException(400, "count от 1 до 5")

    c = CASES[case_id]
    total_cost = c["price"] * count
    if user.balance < total_cost:
        raise HTTPException(400, f"Нужно {total_cost:,} ₽")

    user.balance -= total_cost
    cars_objs = []
    total_xp = 0

    for _ in range(count):
        car_data = roll_case_car(case_id)
        xp_g = XP_BY_RARITY.get(car_data["rarity"], 10)
        add_xp(user, xp_g)
        total_xp += xp_g
        user.total_cars_obtained += 1
        car = make_car(user, car_data)
        db.add(car)
        cars_objs.append(car)

    db.commit()
    db.refresh(user)
    for c_ in cars_objs:
        db.refresh(c_)

    return {
        "cars": [car_to_dict(c_) for c_ in cars_objs],
        "car": car_to_dict(cars_objs[0]),
        "balance": user.balance,
        "level": user.level,
        "xp": user.xp,
        "xp_next": xp_for_next_level(user.level),
        "xp_gained": total_xp,
    }


@app.post("/api/upgrade/{tg_id}/{car_id}/{part}")
def upgrade_part(tg_id: int, car_id: int, part: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if part not in UPGRADE_PARTS:
        raise HTTPException(400, "Unknown part")

    car = db.query(UserCar).filter(UserCar.id == car_id, UserCar.user_id == user.id).first()
    if not car:
        raise HTTPException(404, "Car not found")

    col = f"{part}_lvl"
    current_lvl = getattr(car, col) or 0
    if current_lvl >= 4:
        raise HTTPException(400, "Максимальный уровень")

    cost = round(car.base_price * UPGRADE_COST_PCT[current_lvl], 2)
    chance = UPGRADE_CHANCES[current_lvl]

    if user.balance < cost:
        raise HTTPException(400, f"Нужно {int(cost):,} ₽")

    user.balance -= cost
    success = random.random() * 100 < chance

    if success:
        setattr(car, col, current_lvl + 1)
        recalc_price(car)

    db.commit()
    db.refresh(user)
    db.refresh(car)

    new_level = getattr(car, col) or 0

    return {
        "success": success,
        "cost": cost,
        "chance": chance,
        "part": part,
        "new_level": new_level,
        "car": car_to_dict(car),
        "balance": user.balance,
    }


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
            raise HTTPException(400, f"Через {remaining // 60} мин {remaining % 60} сек")

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
        car_data = roll_case_car(value)
        car = make_car(user, car_data)
        db.add(car)
        result_text = f"Машина: {car_data['brand']} {car_data['model']}"

    user.last_wheel = now
    db.commit()
    db.refresh(user)

    return {
        "result_text": result_text,
        "balance": user.balance,
        "tickets": user.tickets,
    }


@app.post("/api/ticket-case/{tg_id}")
def open_ticket_case(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.tickets < TICKET_CASE_COST:
        raise HTTPException(400, f"Нужно {TICKET_CASE_COST} 🎫")

    user.tickets -= TICKET_CASE_COST
    rewards = [
        ("money", 100_000, 25),
        ("money", 300_000, 15),
        ("tickets", 1, 15),
        ("xp", 200, 15),
        ("xp", 1000, 7),
        ("car", None, 23),
    ]
    weights = [r[2] for r in rewards]
    reward = random.choices(rewards, weights=weights, k=1)[0]
    kind, value, _ = reward

    result = {}
    if kind == "money":
        user.balance += value
        result = {"type": "money", "label": f"+{value:,} ₽"}
    elif kind == "tickets":
        user.tickets += value
        result = {"type": "tickets", "label": f"+{value} 🎫"}
    elif kind == "xp":
        add_xp(user, value)
        result = {"type": "xp", "label": f"+{value} XP"}
    elif kind == "car":
        car_data = roll_case_car("case50")
        car = make_car(user, car_data)
        db.add(car)
        user.total_cars_obtained += 1
        db.flush()
        result = {
            "type": "car",
            "label": f"{car_data['brand']} {car_data['model']}",
            "car": car_to_dict(car),
        }

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
    sell = round(car.price * 0.7, 2)
    user.balance += sell
    db.delete(car)
    db.commit()
    db.refresh(user)
    return {"sold_price": sell, "new_balance": user.balance}


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
            r = 24 * 3600 - delta.total_seconds()
            raise HTTPException(400, f"Бонус через {int(r//3600)} ч {int((r%3600)//60)} мин")

    user.balance += BONUS_MONEY
    user.last_bonus = now
    db.commit()
    db.refresh(user)
    return {"bonus_money": BONUS_MONEY, "new_balance": user.balance}
