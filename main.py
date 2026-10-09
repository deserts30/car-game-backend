import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from game_logic import roll_car
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
    # Запускаем бота прямо в loop FastAPI (в главном потоке)
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

users = {}


class InitData(BaseModel):
    tg_id: int
    username: str = "player"


@app.get("/")
def root():
    return {"message": "Car Game API + Bot running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth")
def auth(data: InitData):
    if data.tg_id not in users:
        users[data.tg_id] = {"balance": 1000, "energy": 10, "cars": []}
    return users[data.tg_id]


@app.post("/api/roll/{tg_id}")
def do_roll(tg_id: int):
    if tg_id not in users:
        raise HTTPException(404, "User not found")
    u = users[tg_id]
    if u["energy"] <= 0:
        raise HTTPException(400, "Нет энергии")
    u["energy"] -= 1
    car = roll_car()
    u["cars"].append(car)
    return {"car": car, "energy": u["energy"], "balance": u["balance"]}


@app.get("/api/garage/{tg_id}")
def garage(tg_id: int):
    return users.get(tg_id, {"cars": []})
