import json
import os
from flask import Flask, request
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

app = Flask(__name__)

def cargar():
    with open("recetas.json", "r", encoding="utf-8") as f:
        return json.load(f)

def guardar(data):
    with open("recetas.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -------- MENU --------
def menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("📋 Menú")
    m.row("➕ Agregar receta", "🗑️ Eliminar receta")
    return m

@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "🍹 Bot listo", reply_markup=menu())

# -------- VER MENU --------
@bot.message_handler(func=lambda m: m.text == "📋 Menú")
def ver_menu(msg):
    recetas = cargar()
    markup = InlineKeyboardMarkup()

    for nombre in recetas:
        markup.add(InlineKeyboardButton(nombre, callback_data=f"ver_{nombre}"))

    bot.send_message(msg.chat.id, "📋 Elige:", reply_markup=markup)

# -------- ELIMINAR --------
@bot.message_handler(func=lambda m: m.text == "🗑️ Eliminar receta")
def eliminar_menu(msg):
    recetas = cargar()
    markup = InlineKeyboardMarkup()

    for nombre in recetas:
        markup.add(InlineKeyboardButton(nombre, callback_data=f"del_{nombre}"))

    bot.send_message(msg.chat.id, "Selecciona para eliminar:", reply_markup=markup)

# -------- CALLBACK --------
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    recetas = cargar()
    data = call.data

    # VER RECETA
    if data.startswith("ver_"):
        nombre = data.replace("ver_", "")

        if nombre in recetas:
            r = recetas[nombre]
            ingredientes = "\n".join([f"- {k}: {v}" for k, v in r["ingredientes"].items()])

            texto = f"""<b>{nombre.upper()}</b>

🥃 Ingredientes:
{ingredientes}

🥤 Vaso: {r["vaso"]}
⚙ Método: {r["metodo"]}
"""
            bot.send_message(call.message.chat.id, texto)

    # PEDIR CONFIRMACION
    elif data.startswith("del_"):
        nombre = data.replace("del_", "")

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Sí eliminar", callback_data=f"confirm_{nombre}"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancel")
        )

        bot.send_message(call.message.chat.id, f"¿Eliminar {nombre}?", reply_markup=markup)

    # CONFIRMAR ELIMINACION
    elif data.startswith("confirm_"):
        nombre = data.replace("confirm_", "")

        if nombre in recetas:
            del recetas[nombre]
            guardar(recetas)
            bot.send_message(call.message.chat.id, "🗑️ Eliminado")

    elif data == "cancel":
        bot.send_message(call.message.chat.id, "Cancelado")

# -------- AGREGAR --------
estado = {}

@bot.message_handler(func=lambda m: m.text == "➕ Agregar receta")
def iniciar_agregar(msg):
    estado[msg.chat.id] = {"paso": 1}
    bot.send_message(msg.chat.id, "Nombre del cóctel:")

@bot.message_handler(func=lambda m: m.chat.id in estado)
def flujo(msg):
    user = estado[msg.chat.id]

    try:
        if user["paso"] == 1:
            user["nombre"] = msg.text.lower()
            user["paso"] = 2
            bot.send_message(msg.chat.id, "Ingredientes:\nej: pisco 4 oz, limón 1 1/2 oz")

        elif user["paso"] == 2:
            ing = {}
            partes = msg.text.split(",")

            for p in partes:
                p = p.strip().split()
                nombre = " ".join(p[:-2])
                cantidad = " ".join(p[-2:])
                ing[nombre] = cantidad

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

            bot.send_message(msg.chat.id, "✅ Guardado", reply_markup=menu())

    except:
        bot.send_message(msg.chat.id, "⚠️ Ejemplo:\npisco 4 oz, limón 1 1/2 oz")

# -------- WEBHOOK --------
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
