import os
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
from chatbot import responder
from database.database import crear_base_datos, guardar_conversacion

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")

# Crear la base de datos automáticamente
crear_base_datos()


def validar_api_key():
    # Estas rutas no requieren API Key
    if request.path == "/" or request.path == "/health":
        return True

    api_key = request.headers.get("X-API-KEY")
    return api_key == API_KEY


@app.before_request
def autenticar():
    if not validar_api_key():
        return jsonify({
            "error": "API Key inválida o no proporcionada"
        }), 401


# Página principal
@app.route("/", methods=["GET"])
def inicio():
    return render_template("index.html")


# Estado de la API
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "OK"
    })


# Versión
@app.route("/version", methods=["GET"])
def version():
    return jsonify({
        "version": "1.0"
    })


# Chat
@app.route("/chat", methods=["POST"])
def chat():

    datos = request.get_json()

    if not datos or "mensaje" not in datos:
        return jsonify({
            "error": "Debes enviar un mensaje"
        }), 400

    mensaje = datos["mensaje"]
    respuesta = responder(mensaje)

    guardar_conversacion(
        "Usuario",
        mensaje,
        respuesta
    )

    return jsonify({
        "respuesta": respuesta
    })


if __name__ == "__main__":
    app.run(debug=True)