import re

from files_and_folders.files import File
from files_and_folders.folders import Folder
from files_and_folders.pdfs import PDF


def extraer_texto_con_pdfplumber(pdf_path):
    texto_completo = ""

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            texto_completo += pagina.extract_text() + "\n"

    return texto_completo

def save_file(file):
    #pdf = PDF(file.path)
    pdf_text = extraer_texto_con_pdfplumber(file.path)
    periodo = ""

    # Buscamos en modelo en el documento
    modelo = re.findall(r"Modelo (\d{3})", pdf_text)
    if len(modelo) > 0:
        modelo = int(modelo[0])
    else:
        raise NameError("No se localiza el modelo en el documento")


    modelos = {"mensual": [111],
               "mensual/trimestral": [115, 123, 303, 349, 216, 309],
               "trimestral": [130, 110],
               "anual": [190, 140, 180, 184, 200, 220, 390, 347, 232, 296, 345]}

    # Buscamos en ejercicio en el documento
    año = re.findall(r'(Ejercicio|período|anual)\s+\D*\b(\b202\d{1})', pdf_text)
    if len(año) > 0:
        ejercicio = año[-1][-1]

    else:
        re.findall(r'(\d{2}/\d{2}/\d{4})([\s\S]+?)(\d{2}/\d{2}/\d{4})', pdf_text)[-1]
        ejercicio = re.findall(r"(20\d{2})", pdf_text)[0]

    # Si el modelo está entre los modelos anuales
    if modelo in modelos["anual"]:
        #nombre_archivo = f"{nif} {nombre} {modelo} {ejercicio[-2:]}.pdf"
        pass

    # Si el modelo es mensual
    elif modelo in modelos["mensual"]:
        mensual = re.findall(
            r"(>?Per[í|i]odo[\s\S]+?)(ENERO|FEBR.|MARZO|ABRIL|MAYO|JUN.|JUL.|AGO.|SET.|OCT.|NOV.|DIC.)", pdf_text)

        mensual_num = re.findall(rf"(>?{ejercicio})\n(01|02|03|04|05|06|07|08|09|10|11|12)", pdf_text)
        mensual_texto = re.findall(
            r"(Periodo\s)(.?)(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)",
            pdf_text, re.IGNORECASE)

        if len(mensual) > 0:
            month_list = {
                'ENERO': 'enero',
                'FEBR.': 'febrero',
                'MARZO': 'marzo',
                'ABRIL': 'abril',
                'MAYO': 'mayo',
                'JUN.': 'junio',
                'JUL.': 'julio',
                'AGO.': 'agosto',
                'SET.': 'septiembre',
                'OCT.': 'octubre',
                'NOV.': 'noviembre',
                'DIC.': 'diciembre'
            }
            try:
                mes = month_list[mensual[0][-1]]
            except:
                mes = month_list[mensual[-1][-1]]
        elif len(mensual_num) > 0:
            month_list = {
                '01': 'enero',
                '02.': 'febrero',
                '03': 'marzo',
                '04': 'abril',
                '05': 'mayo',
                '06': 'junio',
                '07': 'julio',
                '08': 'agosto',
                '09': 'septiembre',
                '10': 'octubre',
                '11': 'noviembre',
                '12': 'diciembre'
            }
            mes = month_list[mensual_num[0][-1]]

        elif len(mensual_texto) > 0:
            try:
                mes = mensual_texto[0][-1]
            except:
                mes = mensual_texto[-1][-1]
        #nombre_archivo = f"{nif} {nombre} {modelo} {mes} {ejercicio[-2:]}.pdf"

    # Si el modelo es trimestral
    elif modelo in modelos["trimestral"]:
        trimestral = re.findall(r'(TRIM\d{1})', pdf_text)
        if len(trimestral) > 0:
            trimestre = trimestral[0].replace("TRIM", "").strip()
            trimestre = f"{trimestre}º trimestre"
            #nombre_archivo = f"{nif} {nombre} {modelo} {trimestre} {ejercicio[-2:]}.pdf"
        else:
            raise Exception("No se localiza el trimestre")

    elif modelo in modelos["mensual/trimestral"]:
        mensual = re.findall(
            r">?Per[í|i]odo[\s\S]+?(ENERO|FEBR.|MARZO|ABRIL|MAYO|JUN.|JUL.|AGO.|SET.|OCT.|NOV.|DIC.)\n", pdf_text)

        mensual_num = re.findall(rf">?{ejercicio}\n(01|02|03|04|05|06|07|08|09|10|11|12)", pdf_text)
        mensual_texto = re.findall(
            r"Periodo\s.?(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)",
            pdf_text, re.IGNORECASE)
        trimestral = re.findall(r'(TRIM\d{1})', pdf_text)

        if len(trimestral) > 0:
            trimestre = trimestral[0].replace("TRIM", "").strip()
            periodo = f"{trimestre}º trimestre"
        elif len(mensual) > 0:
            month_list = {
                'ENERO': 'enero',
                'FEBR.': 'febrero',
                'MARZO': 'marzo',
                'ABRIL': 'abril',
                'MAYO': 'mayo',
                'JUN.': 'junio',
                'JUL.': 'julio',
                'AGO.': 'agosto',
                'SET.': 'septiembre',
                'OCT.': 'octubre',
                'NOV.': 'noviembre',
                'DIC.': 'diciembre'
            }
            try:
                periodo = month_list[mensual[0]]
            except:
                periodo = month_list[mensual[-1]]
        elif len(mensual_num) > 0:
            month_list = {
                '01': 'enero',
                '02.': 'febrero',
                '03': 'marzo',
                '04': 'abril',
                '05': 'mayo',
                '06': 'junio',
                '07': 'julio',
                '08': 'agosto',
                '09': 'septiembre',
                '10': 'octubre',
                '11': 'noviembre',
                '12': 'diciembre'
            }
            periodo = month_list[mensual_num[0]]
        elif len(mensual_texto) > 0:
            try:
                periodo = mensual_texto[0]
            except:
                periodo = mensual_texto[-1]
        else:
            raise NameError("No se localiza el Periodo en el documento")
    re.findall(r"complementaria[\s\S]+?(✔|✖)[\s\S]+?sustitutiva", pdf_text)
        #nombre_archivo = f"{nif} {nombre} {modelo} {periodo} {ejercicio[-2:]}.pdf"
    """
    if len(re.findall(r"complementaria[\s\S]+?(✔|✖)[\s\S]+?sustitutiva", pdf_text)) > 0:
        #nombre_archivo = nombre_archivo.replace(".pdf", "_complementaria.pdf")
    elif len(re.findall(r"sustitutiva[\s\S]+?(✔|✖)", pdf_text)) > 0:
        #nombre_archivo = nombre_archivo.replace(".pdf", "_sustitutiva.pdf")
    """
    print(modelo, ejercicio, periodo, file.file_name)
    """
    folder_path = DOWNLOAD_FOLDER + f"\\{cod_cliente}\\IMPUESTOS\\{ejercicio}"
    # Folder(folder_path)

    file.rename(nombre_archivo)
    Folder(COMMON_FOLDER)
    if not File(COMMON_FOLDER + nombre_archivo).exists:
        # file.move(folder_path)
        file.move(COMMON_FOLDER)
    # if not File(folder_path  +"\\" + nombre_archivo).exists:
    #    #file.move(folder_path)
    #    print(folder_path  +"\\" + nombre_archivo)
    return (modelo, periodo, file.path)
    """

import fitz  # PyMuPDF

# Abre el archivo PDF

import fitz  # PyMuPDF

import pdfplumber

def extraer_texto_con_pdfplumber(pdf_path):
    texto_completo = ""

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            texto_completo += pagina.extract_text() + "\n"

    return texto_completo


#for file in Folder("M:\PRUEBAS_2023\Incorrecta").file_list(".pdf"):
#    save_file(file)

file = File("/Users/enriquecrespodebenito/Desktop/B06993562 NIRE REFORMAK, S.L. 347 25.pdf")
save_file(file)