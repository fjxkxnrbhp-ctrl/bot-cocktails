import json
from flask import Flask

app = Flask(__name__)

with open("recetas.json", "r", encoding="utf-8") as f:
    recetas = json.load(f)

@app.route("/")
def home():
    return "Bot de cócteles funcionando 🍹"

@app.route("/receta/<nombre>")
def receta(nombre):
    nombre = nombre.lower()

    if nombre in recetas:
        return recetas[nombre]

    return {"error": "No existe esa receta"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
