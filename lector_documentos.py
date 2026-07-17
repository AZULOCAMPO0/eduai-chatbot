import os
import fitz  # PyMuPDF
from docx import Document


CARPETA_DOCUMENTOS = "documentos"


def leer_pdf(ruta):
    texto = ""

    pdf = fitz.open(ruta)

    for pagina in pdf:
        texto += pagina.get_text()

    pdf.close()

    return texto


def leer_docx(ruta):
    texto = ""

    doc = Document(ruta)

    for parrafo in doc.paragraphs:
        texto += parrafo.text + "\n"

    return texto


def cargar_documentos():

    documentos = {}

    if not os.path.exists(CARPETA_DOCUMENTOS):
        return documentos

    for archivo in os.listdir(CARPETA_DOCUMENTOS):

        ruta = os.path.join(CARPETA_DOCUMENTOS, archivo)

        if archivo.lower().endswith(".pdf"):
            documentos[archivo] = leer_pdf(ruta)

        elif archivo.lower().endswith(".docx"):
            documentos[archivo] = leer_docx(ruta)

    return documentos


def buscar_respuesta(pregunta):

    documentos = cargar_documentos()

    pregunta = pregunta.lower()

    for nombre, texto in documentos.items():

        if pregunta in texto.lower():

            return f"Según el documento '{nombre}':\n\n{texto[:800]}..."

    return None