import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from game_logic import roll_car
from models import init_db, get_db, User, UserCar

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==== Telegram Bot ====
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


# ==== FastAPI ====
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицы в БД при старте
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


class InitData(BaseModel):
    tg_id: int
    username: str = "player"


def user_to_dict(u: User):
    return {
        "balance": u.balance,
        "energy": u.energy,
        "cars": [
            {
                "id": c.id,
                "brand": c.brand,
                "model": c.model,
                "year": c.year,
                "color": c.color,
                "rarity": c.rarity,
                "condition": c.condition,
                "price": c.price,
            }
            for c in u.cars
        ],
    }


@app.get("/")
def root():
    return {"message": "Car Game API + Bot running"}


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}


@app.post("/api/auth")
def auth(data: InitData, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == data.tg_id).first()

    if not user:
        user = User(tg_id=data.tg_id, username=data.username)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user_to_dict(user)


@app.post("/api/roll/{tg_id}")
def do_roll(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if user.energy <= 0:
        raise HTTPException(400, "Нет энергии")

    user.energy -= 1
    car_data = roll_car()

    car = UserCar(
        user_id=user.id,
        brand=car_data["brand"],
        model=car_data["model"],
        year=car_data["year"],
        color=car_data["color"],
        rarity=car_data["rarity"],
        condition=car_data["condition"],
        price=car_data["price"],
    )
    db.add(car)
    db.commit()
    db.refresh(user)

    return {
        "car": car_data,
        "energy": user.energy,
        "balance": user.balance,
    }


@app.get("/api/garage/{tg_id}")
def garage(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        return {"cars": []}

    return {
        "cars": [
            {
                "id": c.id,
                "brand": c.brand,
                "model": c.model,
                "year": c.year,
                "color": c.color,
                "rarity": c.rarity,
                "condition": c.condition,
                "price": c.price,
            }
            for c in user.cars
        ]
    }

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

    # Игрок получает 70% от цены
    sell_price = round(car.price * 0.7, 2)
    user.balance += sell_price

    db.delete(car)
    db.commit()
    db.refresh(user)

    return {
        "sold_price": sell_price,
        "new_balance": user.balance,
    }
