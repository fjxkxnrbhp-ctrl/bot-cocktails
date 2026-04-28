import json
import os
from flask import Flask, request
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# ---------- ARCHIVO ----------
def cargar():
    with open("recetas.json", "r", encoding="utf-8") as f:
        return json.load(f)

def guardar(data):
    with open("recetas.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------- MENU ----------
def menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(
        KeyboardButton("📋 Ver cócteles"),
        KeyboardButton("➕ Agregar receta")
    )
    return m

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "🍹 Bot bartender listo", reply_markup=menu())

# ---------- VER COCTELES (BOTONES) ----------
@bot.message_handler(func=lambda m: m.text == "📋 Ver cócteles")
def ver(msg):
    recetas = cargar()
    markup = InlineKeyboardMarkup()

    for nombre in recetas.keys():
        markup.add(InlineKeyboardButton(nombre, callback_data=nombre))

    bot.send_message(msg.chat.id, "Selecciona un cóctel:", reply_markup=markup)

# ---------- RESPUESTA BOTONES ----------
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    recetas = cargar()
    nombre = call.data

    if nombre in recetas:
        r = recetas[nombre]

        ingredientes = "\n".join(
            [f"- {k}: {v}" for k, v in r["ingredientes"].items()]
        )

        respuesta = f"""🍹 {nombre.upper()}

🥃 Ingredientes:
{ingredientes}

🥤 Vaso: {r["vaso"]}
⚙ Método: {r["metodo"]}
"""
        bot.send_message(call.message.chat.id, respuesta)

# ---------- AGREGAR RECETA ----------
estado = {}

@bot.message_handler(func=lambda m: m.text == "➕ Agregar receta")
def agregar(msg):
    estado[msg.chat.id] = {"paso": 1}
    bot.send_message(msg.chat.id, "Nombre del cóctel:")

@bot.message_handler(func=lambda m: m.chat.id in estado)
def flujo(msg):
    user = estado[msg.chat.id]

    try:
        if user["paso"] == 1:
            user["nombre"] = msg.text.lower()
            user["paso"] = 2
            bot.send_message(msg.chat.id, "Ingredientes (ej: ron:2 oz, limón:1 oz)")

        elif user["paso"] == 2:
            ing = {}
            for i in msg.text.split(","):
                k, v = i.split(":")
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

            bot.send_message(msg.chat.id, "✅ Receta guardada")

    except:
        bot.send_message(msg.chat.id, "⚠️ Error, intenta de nuevo")
        del estado[msg.chat.id]

# ---------- WEBHOOK ----------
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
