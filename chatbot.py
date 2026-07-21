from lector_documentos import buscar_respuesta


def responder(mensaje):
    """
    Función principal del chatbot.
    Primero responde conversaciones básicas.
    Después consulta la base de conocimiento (PDF/Word).
    """

    mensaje = mensaje.lower().strip()

    # Saludo
    if mensaje == "hola":
        return "Hola. Soy EduAI. ¿En qué puedo ayudarte?"

    # Despedida
    elif mensaje == "adiós" or mensaje == "adios":
        return "¡Hasta luego! Que tengas un excelente día."

    # Agradecimiento
    elif mensaje == "gracias":
        return "Con gusto. Estoy aquí para ayudarte."

    # Quién eres
    elif mensaje == "quién eres" or mensaje == "quien eres":
        return (
            "Soy EduAI, un tutor virtual desarrollado con Python y Flask "
            "para apoyar a los estudiantes."
        )

    # Qué puedes hacer
    elif mensaje == "qué puedes hacer" or mensaje == "que puedes hacer":
        return (
            "Puedo responder preguntas programadas y también buscar "
            "información dentro de los documentos PDF y Word que se "
            "encuentran en la carpeta 'documentos'."
        )

    # Buscar en la base de conocimiento
    respuesta_documento = buscar_respuesta(mensaje)

    if respuesta_documento:
        return respuesta_documento

    # Python
    if mensaje == "¿qué es python?" or mensaje == "que es python":
        return (
            "Python es un lenguaje de programación de alto nivel "
            "muy utilizado para desarrollar aplicaciones web, "
            "inteligencia artificial y automatización."
        )

    # Base de datos
    elif mensaje == "¿qué es una base de datos?" or mensaje == "que es una base de datos":
        return (
            "Una base de datos es un sistema que permite almacenar, "
            "organizar y consultar información."
        )

    # Respuesta por defecto
    return (
        "Lo siento, aún no encontré la respuesta en mis documentos "
        "ni en mi base de conocimientos."
    )