import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from game_logic import roll_car

app = FastAPI()

# Разрешаем запросы откуда угодно (нужно для Mini App)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Простое хранилище в памяти (для продакшена потом заменим на базу данных)
users = {}


class InitData(BaseModel):
    tg_id: int
    username: str = "player"


@app.get("/health")
def health():
    """Эндпоинт для UptimeRobot, чтобы сервер не засыпал."""
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Car Game API is running"}


@app.post("/api/auth")
def auth(data: InitData):
    """Регистрация/вход игрока."""
    if data.tg_id not in users:
        users[data.tg_id] = {
            "balance": 1000,
            "energy": 10,
            "cars": [],
        }
    return users[data.tg_id]


@app.post("/api/roll/{tg_id}")
def do_roll(tg_id: int):
    """Выбить машину."""
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
    """Получить гараж игрока."""
    return users.get(tg_id, {"cars": []})


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
