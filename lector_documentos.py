import os
import re
import unicodedata
import fitz  # PyMuPDF
import docx

# Ruta ABSOLUTA basada en la ubicación de este archivo, no en el CWD del proceso.
# Esto evita que Render, gunicorn o un IDE arrancando desde otra carpeta
# no encuentren la carpeta "documentos".
CARPETA_DOCUMENTOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "documentos"
)

# Palabras comunes que no aportan significado en la búsqueda.
# Definida a nivel de módulo para no reconstruir el set en cada mensaje.
PALABRAS_VACIAS = {
    "que", "qué", "es", "el", "la", "los", "las",
    "un", "una", "unos", "unas",
    "de", "del", "al", "en", "por", "para",
    "con", "sin", "y", "o", "a", "me",
    "explica", "explicame", "explícame",
}

# Cache en memoria. Se construye una sola vez (al primer uso) y se reutiliza
# en cada mensaje del chat, en vez de releer los PDF en cada request.
_INDICE = None


def normalizar_texto(texto):
    """
    Minúsculas, sin acentos, sin saltos de línea/espacios irregulares.
    Necesario porque PyMuPDF a veces corta palabras al final de línea
    y porque una pregunta con o sin acentos debe encontrar lo mismo.
    """
    if not texto:
        return ""

    texto = texto.lower()

    # Quitar acentos (á -> a, é -> e, í -> i, ó -> o, ú -> u)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))

    # Unir palabras partidas por guion de fin de línea: "relacio-\nnal" -> "relacional"
    texto = texto.replace("-\n", "")

    # Colapsar saltos de línea y espacios múltiples en uno solo
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def limpiar_saltos_de_linea(texto):
    """
    El PDF trae un '\n' por cada línea visual del libro (no por párrafo),
    lo que hace que el texto se vea 'escalonado' al mostrarlo. Esto une esas
    líneas sueltas en párrafos fluidos, dejando como salto de línea real
    únicamente las líneas en blanco (separación de párrafo genuina).
    """
    if not texto:
        return texto

    # Un solo "\n" (no seguido ni precedido de otro "\n") se convierte en
    # espacio; "\n\n" (párrafo real) se conserva.
    texto = re.sub(r"(?<!\n)\n(?!\n)", " ", texto)

    # Colapsar espacios múltiples que haya dejado el reemplazo anterior
    texto = re.sub(r"[ \t]+", " ", texto)

    # Colapsar 3+ saltos de línea seguidos en un solo salto de párrafo
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()


def leer_pdf(ruta):
    texto = ""

    try:
        pdf = fitz.open(ruta)

        for pagina in pdf:
            # sort=True ayuda a mantener el orden de lectura correcto
            # en documentos con columnas o tablas.
            texto += pagina.get_text("text", sort=True)
            texto += "\n"

        pdf.close()

    except Exception as e:
        print(f"[lector_documentos] ERROR leyendo PDF {ruta}: {e}")

    return texto


def leer_docx(ruta):
    texto = ""

    try:
        documento = docx.Document(ruta)

        for parrafo in documento.paragraphs:
            texto += parrafo.text + "\n"

    except Exception as e:
        print(f"[lector_documentos] ERROR leyendo Word {ruta}: {e}")

    return texto


def es_fragmento_indice(texto):
    """
    Detecta fragmentos que son tabla de contenidos / índice del libro
    (líneas del tipo "2.2. Estructura de datos . . . . . . . . 16").
    Estos fragmentos hacen match fácil por título de capítulo, pero casi
    nunca son la explicación que el usuario busca.
    """
    # 4 o más "puntos suspensivos" (con o sin espacios entre ellos) es
    # el patrón típico de una línea de índice con líder de puntos.
    return bool(re.search(r"(\.\s*){4,}", texto))


def _ajustar_a_limite_oracion(texto, posicion, buscar_hacia_atras, ventana=150):
    """
    Ajusta 'posicion' al punto (o salto de línea doble) más cercano dentro
    de una ventana, para no cortar el fragmento a mitad de una frase.
    buscar_hacia_atras=True busca el corte anterior (para el inicio del
    fragmento); False busca hacia adelante (para el final).
    """
    longitud = len(texto)
    posicion = max(0, min(posicion, longitud))

    if buscar_hacia_atras:
        desde = max(0, posicion - ventana)
        segmento = texto[desde:posicion]
        # Busca el último ". " o "\n\n" dentro de la ventana
        candidatos = [segmento.rfind(". "), segmento.rfind("\n\n")]
        mejor = max(candidatos)
        if mejor != -1:
            return desde + mejor + 2  # justo después del punto/espacio
        return posicion
    else:
        hasta = min(longitud, posicion + ventana)
        segmento = texto[posicion:hasta]
        candidatos = [segmento.find(". "), segmento.find("\n\n")]
        candidatos = [c for c in candidatos if c != -1]
        if candidatos:
            return posicion + min(candidatos) + 1  # incluye el punto
        return posicion


def dividir_en_fragmentos(texto_original, tamano=700, solape=100):
    """
    Divide un texto largo en fragmentos solapados, ajustando los cortes al
    límite de oración más cercano para no partir frases a la mitad. Esto
    sirve para:
    1) devolver contexto relevante y no un PDF entero de golpe.
    2) que el score de coincidencias sea por sección, no por documento completo.
    """
    fragmentos = []
    inicio = 0
    longitud = len(texto_original)

    if longitud == 0:
        return fragmentos

    while inicio < longitud:
        fin_objetivo = min(inicio + tamano, longitud)

        if fin_objetivo < longitud:
            fin = _ajustar_a_limite_oracion(texto_original, fin_objetivo, buscar_hacia_atras=False)
        else:
            fin = longitud

        inicio_ajustado = inicio
        if inicio > 0:
            inicio_ajustado = _ajustar_a_limite_oracion(texto_original, inicio, buscar_hacia_atras=True)

        fragmento = texto_original[inicio_ajustado:fin].strip()
        if fragmento:
            fragmentos.append(fragmento)

        if fin >= longitud:
            break

        inicio = max(fin - solape, inicio_ajustado + 1)

    return fragmentos


def construir_indice():
    """
    Lee todos los documentos de la carpeta UNA sola vez y arma una lista
    de fragmentos indexados:
        [{"documento": nombre, "texto": original, "texto_normalizado": ...}, ...]
    """
    indice = []

    if not os.path.exists(CARPETA_DOCUMENTOS):
        print(f"[lector_documentos] ERROR: no existe la carpeta {CARPETA_DOCUMENTOS}")
        return indice

    archivos = sorted(os.listdir(CARPETA_DOCUMENTOS))

    if not archivos:
        print(f"[lector_documentos] ADVERTENCIA: la carpeta {CARPETA_DOCUMENTOS} está vacía.")

    for archivo in archivos:

        ruta = os.path.join(CARPETA_DOCUMENTOS, archivo)

        if archivo.lower().endswith(".pdf"):
            texto_crudo = leer_pdf(ruta)
        elif archivo.lower().endswith(".docx"):
            texto_crudo = leer_docx(ruta)
        else:
            continue

        print(f"[lector_documentos] {archivo}: {len(texto_crudo)} caracteres extraídos")

        if len(texto_crudo.strip()) == 0:
            print(
                f"[lector_documentos] ADVERTENCIA: {archivo} no produjo texto. "
                f"Es probable que sea un PDF escaneado (imagen) y necesite OCR "
                f"(por ejemplo con pytesseract), o que tenga una fuente embebida "
                f"sin mapa Unicode correcto."
            )
            continue

        texto_crudo = limpiar_saltos_de_linea(texto_crudo)

        for fragmento in dividir_en_fragmentos(texto_crudo):
            indice.append({
                "documento": archivo,
                "texto": fragmento,
                "texto_normalizado": normalizar_texto(fragmento),
                "es_indice": es_fragmento_indice(fragmento),
            })

    total_docs = len({f["documento"] for f in indice})
    print(f"[lector_documentos] Índice construido: {len(indice)} fragmentos de {total_docs} documento(s).")

    return indice


def obtener_indice(forzar_recarga=False):
    """
    Devuelve el índice en cache. Solo lo reconstruye si aún no existe
    o si se pide explícitamente (forzar_recarga=True), por ejemplo tras
    actualizar los PDF sin reiniciar el servidor.
    """
    global _INDICE

    if _INDICE is None or forzar_recarga:
        _INDICE = construir_indice()

    return _INDICE


def buscar_respuesta(pregunta, minimo_coincidencias=1):
    """
    Busca por coincidencia de palabras clave (scoring por fragmento),
    en vez de exigir que la frase completa exista tal cual en el texto.
    Devuelve el fragmento con más palabras clave coincidentes.
    """
    indice = obtener_indice()

    if not indice:
        return None

    pregunta_normalizada = normalizar_texto(pregunta)

    palabras_clave = [
        palabra for palabra in pregunta_normalizada.split()
        if len(palabra) > 2 and palabra not in PALABRAS_VACIAS
    ]

    if not palabras_clave:
        return None

    mejor_fragmento = None
    mejor_score = 0

    for entrada in indice:
        score = sum(
            1 for palabra in palabras_clave
            if palabra in entrada["texto_normalizado"]
        )

        if score == 0:
            continue

        # Penalizamos fuerte los fragmentos de tabla de contenidos: solo
        # ganan si ningún fragmento de contenido real hizo match.
        score_efectivo = score - (1000 if entrada["es_indice"] else 0)

        if mejor_fragmento is None or score_efectivo > (
            mejor_score - (1000 if mejor_fragmento["es_indice"] else 0)
        ):
            mejor_score = score
            mejor_fragmento = entrada

    if mejor_fragmento is None or mejor_score < minimo_coincidencias:
        return None

    return (
        f"📄 Información encontrada en: {mejor_fragmento['documento']}\n\n"
        f"{mejor_fragmento['texto'].strip()}"
    )


if __name__ == "__main__":
    # Diagnóstico standalone: ejecuta "python lector_documentos.py"
    # Esto te dice de forma inequívoca si el problema es de extracción/ruta
    # o si ya funciona y el problema estaba en cómo se llamaba desde el chatbot.

    indice = obtener_indice(forzar_recarga=True)

    print("\n========================")
    print("RESUMEN DEL ÍNDICE")
    print("========================")

    conteo = {}
    for entrada in indice:
        conteo[entrada["documento"]] = conteo.get(entrada["documento"], 0) + 1

    if not conteo:
        print("No se generó ningún fragmento. Revisa los mensajes de error/advertencia de arriba.")
    else:
        for doc, cantidad in conteo.items():
            print(f"• {doc}: {cantidad} fragmentos")

    for prueba in ["modelo relacional", "sql"]:
        resultado = buscar_respuesta(prueba)
        print(f"\n--- Prueba: '{prueba}' ---")
        print(resultado if resultado else "No se encontró nada (revisa el índice arriba).")