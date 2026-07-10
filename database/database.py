import sqlite3


def crear_base_datos():
    conexion = sqlite3.connect("database/eduai.db")
    cursor = conexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        mensaje TEXT,
        respuesta TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conexion.commit()
    conexion.close()


def guardar_conversacion(usuario, mensaje, respuesta):
    conexion = sqlite3.connect("database/eduai.db")
    cursor = conexion.cursor()

    cursor.execute("""
    INSERT INTO conversaciones(usuario, mensaje, respuesta)
    VALUES (?, ?, ?)
    """, (usuario, mensaje, respuesta))

    conexion.commit()
    conexion.close()