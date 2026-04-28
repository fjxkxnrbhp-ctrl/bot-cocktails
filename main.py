import json
import os
from flask import Flask, request
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# ---- ARCHIVO DE RECETAS ----
def cargar():
    with open("recetas.json", "r", encoding="utf-8") as f:
        return json.load(f)

def guardar(data):
    with open("recetas.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---- MENU ----
def menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(
        KeyboardButton("📋 Ver cócteles"),
        KeyboardButton("🔍 Buscar"),
        KeyboardButton("➕ Agregar receta")
    )
    return m

# ---- START ----
@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "🍹 Bot listo", reply_markup=menu())

# ---- VER LISTA ----
@bot.message_handler(func=lambda m: m.text == "📋 Ver cócteles")
def ver(msg):
    recetas = cargar()
    lista = "\n".join([f"• {k}" for k in recetas.keys()])
    bot.send_message(msg.chat.id, "📋 Cócteles:\n" + lista)

# ---- BUSCAR ----
@bot.message_handler(func=lambda m: m.text == "🔍 Buscar")
def buscar(msg):
    bot.send_message(msg.chat.id, "Escribe el nombre:")

# ---- RESPUESTA ----
@bot.message_handler(func=lambda m: True)
def responder(msg):
    texto = msg.text.lower()
    recetas = cargar()

    if texto in recetas:
        r = recetas[texto]
        ingredientes = "\n".join([f"- {k}: {v}" for k,v in r["ingredientes"].items()])
        respuesta = f"""🍹 {texto.upper()}

🥃 Ingredientes:
{ingredientes}

🥤 Vaso: {r["vaso"]}
⚙ Método: {r["metodo"]}
"""
        bot.send_message(msg.chat.id, respuesta)
    else:
        bot.send_message(msg.chat.id, "No encontrado ❌")

# ---- AGREGAR ----
estado = {}

@bot.message_handler(func=lambda m: m.text == "➕ Agregar receta")
def agregar(msg):
    estado[msg.chat.id] = {"paso": 1}
    bot.send_message(msg.chat.id, "Nombre del cóctel:")

@bot.message_handler(func=lambda m: m.chat.id in estado)
def flujo(msg):
    user = estado[msg.chat.id]

    if user["paso"] == 1:
        user["nombre"] = msg.text.lower()
        user["paso"] = 2
        bot.send_message(msg.chat.id, "Ingredientes (ej: ron:2 oz, limón:1 oz)")

    elif user["paso"] == 2:
        ing = {}
        for i in msg.text.split(","):
            k,v = i.split(":")
            ing[k.strip()] = v.strip()
        user["ingredientes"] = ing
        user["paso"] = 3
        bot.send_message(msg.chat.id, "Vaso:")

    elif user["paso"] == 3:
        user["vaso"] = msg.text
        user["paso"] = 4
        bot.send_message(msg.chat.id, "Método:")

    elif user["paso"] == 4:
        user["metodo"] = msg.text

        recetas = cargar()
        recetas[user["nombre"]] = {
            "ingredientes": user["ingredientes"],
            "vaso": user["vaso"],
            "metodo": user["metodo"]
        }

        guardar(recetas)
        del estado[msg.chat.id]

        bot.send_message(msg.chat.id, "✅ Guardado")

# ---- WEBHOOK ----
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok"

@app.route("/")
def home():
    return "Bot activo"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=os.getenv("RAILWAY_STATIC_URL") + "/" + TOKEN)
    app.run(host="0.0.0.0", port=8080)
