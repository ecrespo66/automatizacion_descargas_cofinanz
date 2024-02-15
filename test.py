from files_and_folders.folders import Folder
from files_and_folders.pdfs import PDF
import re
import pandas as pd
import os



def obtener_archivos_en_carpeta(carpeta_padre):
    archivos = []
    for carpeta_actual, _, archivos_en_carpeta in os.walk(carpeta_padre):
        for archivo in archivos_en_carpeta:
            ruta_completa = os.path.join(carpeta_actual, archivo)
            archivos.append(ruta_completa)
    return archivos


def read_file(file):
    if ".pdf" in file:
        pdf = PDF(file)
        pdf_text = pdf.read_pdf()
        año = re.findall('Ejercicio([\s\S]+?)(202\d{1})', pdf_text)
        if len(año) > 0:
            ejercicio = año[0][-1]
        else:
            año

        trimestral = re.findall('(TRIM\d{1})', pdf_text)
        if len(trimestral) > 0:
            periodo = trimestral[0]
        else:
            month_list = {
                'ENE.': 1,
                'FEB.': 2,
                'MAR.': 3,
                'ABR.': 4,
                'MAY.': 5,
                'JUN.': 6,
                'JUL.': 7,
                'AGO.': 8,
                'SEP.': 9,
                'OCT.': 10,
                'NOV.': 11,
                'DIC.': 12
            }
            if len(re.findall(r"(>?Per[í|i]odo[\s\S]+?)([A-Z]{3}\.)", pdf_text)) > 0:
                match = re.findall(r"(>?Per[í|i]odo[\s\S]+?)([A-Z]{3}\.)", pdf_text)[0][-1]
            else:
                match = "RRR"
            if match in list(month_list.keys()):
                periodo = month_list[re.findall(r"(>?Per[í|i]odo[\s\S]+?)([A-Z]{3}\.)", pdf_text)[0][-1]]
            elif len(re.findall(f"(>?{ejercicio})\n(01|02|03|04|05|06|07|08|09|10|11|12)", pdf_text)) > 0:
                periodo = re.findall(f"(>?{ejercicio})\n(01|02|03|04|05|06|07|08|09|10|11|12)", pdf_text)[0][-1]
            elif len(re.findall(
                    r'(Periodo\s)(.?)(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
                    pdf_text, re.IGNORECASE)):
                meses_dict = {
                    'ENERO': 1,
                    'FEBRERO': 2,
                    'MARZO': 3,
                    'ABRIL': 4,
                    'MAYO': 5,
                    'JUNIO': 6,
                    'JULIO': 7,
                    'AGOSTO': 8,
                    'SEPTIEMBRE': 9,
                    'OCTUBRE': 10,
                    'NOVIEMBRE': 11,
                    'DICIEMBRE': 12
                }
                month = re.findall(
                    r'(Periodo\s)(.?)(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
                    pdf_text, re.IGNORECASE)[0][-1]
                periodo = meses_dict[month.upper()]

            else:
                periodo = "ANUAL"

        return {"File": file, 'Ejercicio': ejercicio, 'Periodo': periodo}


folder = Folder("Z:\Descargas")


"""
rows = []
for file in obtener_archivos_en_carpeta(folder.path):
    data = read_file(file)
    if data:
        rows.append(data)

f = pd.DataFrame(rows)
file = f[(f['Periodo'] == 'ANUAL') & (~f['File'].str.contains('CIERRE'))].reset_index(drop=True)["File"][3]
"""


for doc in Folder("Z:\\COMPLEMENTARIAS Y SUSTITUTIVAS").file_list(".pdf"):
    pdf = PDF(doc.path)
    pdf_text = pdf.read_pdf()

    check =re.findall("(✔|✖)", pdf_text, re.IGNORECASE)
    if len(check) > 0:
        complementaria = re.findall("complementaria", pdf_text, re.IGNORECASE)
        sustitutiva = re.findall("sustitutiva", pdf_text, re.IGNORECASE)
    print(doc.file_name, complementaria, sustitutiva)

