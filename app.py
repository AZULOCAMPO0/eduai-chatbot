import os
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
from flask_cors import CORS

from chatbot import responder
from database.database import crear_base_datos, guardar_conversacion

# ==============================
# Cargar variables de entorno
# ==============================

load_dotenv()

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("API_KEY")

# Crear la base de datos automáticamente
crear_base_datos()


# ==============================
# Validación de API KEY
# ==============================

def validar_api_key():

    # Estas rutas son públicas
    # (se agregó "/version" porque tú mismo lo documentas como endpoint
    # público y antes no estaba en la lista, así que devolvía 401)
    if request.path in ["/", "/health", "/version", "/chat"]:
        return True

    api_key = request.headers.get("X-API-KEY")

    return api_key == API_KEY


@app.before_request
def autenticar():

    if not validar_api_key():

        return jsonify({
            "error": "API Key inválida o no proporcionada"
        }), 401


# ==============================
# Página principal
# ==============================

@app.route("/", methods=["GET"])
def inicio():

    return render_template("index.html")


# ==============================
# Estado de la API
# ==============================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "OK"
    })


# ==============================
# Versión
# ==============================

@app.route("/version", methods=["GET"])
def version():

    return jsonify({
        "version": "1.0"
    })


# ==============================
# Chat principal
# ==============================

@app.route("/chat", methods=["POST"])
def chat():

    datos = request.get_json()

    if not datos:

        return jsonify({
            "error": "No se recibieron datos."
        }), 400

    mensaje = datos.get("mensaje", "").strip()

    if mensaje == "":

        return jsonify({
            "error": "Debes escribir un mensaje."
        }), 400

    respuesta = responder(mensaje)

    guardar_conversacion(
        "Usuario",
        mensaje,
        respuesta
    )

    return jsonify({
        "respuesta": respuesta
    })


# ==============================
# Inicio de la aplicación
# ==============================

if __name__ == "__main__":

    puerto = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=puerto,
        debug=False
    )