def responder(mensaje):
    mensaje = mensaje.lower()

    if mensaje == "hola":
        return "Hola. Soy EduAI. ¿En qué puedo ayudarte?"

    elif mensaje == "¿qué es python?" or mensaje == "que es python":
        return "Python es un lenguaje de programación de alto nivel muy utilizado para desarrollar aplicaciones web, inteligencia artificial y automatización."

    elif mensaje == "¿qué es una base de datos?" or mensaje == "que es una base de datos":
        return "Una base de datos es un sistema que permite almacenar, organizar y consultar información."

    elif mensaje == "adiós" or mensaje == "adios":
        return "¡Hasta luego! Que tengas un excelente día."

    else:
        return "Lo siento, aún no conozco la respuesta a esa pregunta."