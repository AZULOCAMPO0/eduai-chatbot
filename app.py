import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")


def validar_api_key():
    # /health queda libre
    if request.path == "/health":
        return True

    api_key = request.headers.get("X-API-KEY")
    return api_key == API_KEY


@app.before_request
def autenticar():
    if not validar_api_key():
        return jsonify({
            "error": "API Key inválida o no proporcionada"
        }), 401


@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "mensaje": "Bienvenido a EduAI"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "OK"
    })


@app.route("/version", methods=["GET"])
def version():
    return jsonify({
        "version": "1.0"
    })


if __name__ == "__main__":
    app.run(debug=True)