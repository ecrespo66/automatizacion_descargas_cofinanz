import math
import re
import threading
import time
from datetime import datetime

import pyautogui
from files_and_folders.files import File
from files_and_folders.folders import Folder
from files_and_folders.pdfs import PDF

from .selectors import AppSelectors as AS


class App:
    def __init__(self, browser):
        self.browser = browser

    @classmethod
    def load_certificate(self):
        time.sleep(10)
        pyautogui.press('enter')

    def login(self):

        self.browser.open("https://www.ebizkaia.eus/es/profesional")
        self.browser.maximize_window()

        if self.browser.element_exists('xpath', AS.ACEPTAR_COOKIES.value):
            self.browser.find_element('xpath', AS.ACEPTAR_COOKIES.value).click()
        self.browser.wait_for_element('xpath', AS.MIS_GESTIONES.value)
        self.browser.find_element('xpath', AS.MIS_GESTIONES.value).click()
        self.browser.wait_for_element('xpath', AS.MIS_EXPEDIENTES.value)
        self.browser.find_element('xpath', AS.MIS_EXPEDIENTES.value).click()
        self.browser.wait_for_element('xpath', AS.CERTIFICADOS_DIGITALES.value, 20)
        thread = threading.Thread(target=self.load_certificate, daemon=True)
        thread.start()
        # self.load_certificate()
        self.browser.find_element('xpath', AS.CERTIFICADOS_DIGITALES.value).click()

    def find_client(self, nif):
        self.browser.wait_for_element('xpath', AS.INPUT_SELECTOR.value, 60)
        self.browser.find_element("xpath", AS.INPUT_SELECTOR.value).click()
        self.browser.find_element("xpath", AS.INPUT_SELECTOR.value).clear()
        self.browser.find_element("xpath", AS.INPUT_SELECTOR.value).send_keys(nif)

        CLIENT_SELECTOR = f"//span[contains(text(),'{nif}')]"
        time.sleep(10)
        if self.browser.element_exists("xpath", CLIENT_SELECTOR):
            self.browser.find_element("xpath", CLIENT_SELECTOR).click()
            self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE.value, timeout=60)
        else:
            return False

    def filter_data(self, start_date, end_date):

        self.browser.wait_for_element_to_be_clickable("xpath", AS.CAMBIAR_BUSQUEDA.value, 30)
        self.browser.find_element('xpath', AS.CAMBIAR_BUSQUEDA.value).click()
        self.browser.wait_for_element("xpath", AS.FECHA_DESDE.value, 30)
        self.browser.find_element("xpath", AS.FECHA_DESDE.value).send_keys(
            start_date)

        self.browser.find_element("xpath", AS.FECHA_HASTA.value).send_keys(
            end_date)
        self.browser.find_element("xpath", AS.BUSCAR.value).click()

        self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE.value, timeout=60)
        time.sleep(5)
        if self.browser.element_exists('xpath', AS.EXPEDIENTES_ENCONTRADOS.value):
            tramites = self.browser.find_elements('xpath', AS.TRAMITES.value)
            return [*range(len(tramites))]
        else:
            return []




    def obtener_informacion_impuesto(self, tramite):
        self.browser.wait_for_element_to_be_clickable('xpath', AS.TRAMITES.value, 10)
        self.browser.find_elements('xpath', AS.TRAMITES.value)[tramite].click()
        self.browser.wait_for_element_to_be_clickable('xpath', AS.TRAMITACION.value, 10)
        self.browser.find_element("xpath", AS.TRAMITACION.value).click()


        impuesto = self.browser.find_element("xpath", AS.NOMBRE_IMPUESTO.value).text
        modelo = self.browser.find_element("xpath", AS.MODELO_TEXTO.value).text
        fecha = self.browser.find_element("xpath", AS.FECHA_APERTURA.value).text
        fecha_apertura = datetime.strptime(fecha, "%d/%m/%Y")
        match = re.findall("M[0-9]+", modelo)
        modelo = int(match[0].replace("M", ""))
        return{"modelo": modelo, "impuesto": impuesto, "fecha_apertura": fecha_apertura}

    def download_document(self):
        self.browser.wait_for_element("xpath", AS.DOCUMENTACION.value, 30)
        self.browser.find_element('xpath', AS.DOCUMENTACION.value).click()
        self.browser.wait_for_element("xpath", AS.DESCARGAR.value, 30)
        if self.browser.element_exists("xpath", AS.NO_RESULTADOS.value):
            return 'No hay resultados'

        download_button = None
        for row in self.browser.find_elements('xpath', "//tr"):
            if "autoliquidación" in row.text or "Presentación" in row.text:
                download_button = row.find_elements("xpath", ".//td")[-1]
                break

        if download_button:
            download_button.click()
        else:
            return 'No hay resultados'
            #self.browser.find_elements('xpath', AS.BOTON_DESCARGA.value)[3].click()
        return True



    def go_back(self):
        self.browser.find_element('xpath', AS.VOLVER.value).click()
        self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE.value, timeout=60)

    def save_file(self, file, nombre, nif, modelo, impuesto):

        pdf = PDF(file.path)
        pdf_text = pdf.read_pdf()


        modelos = {"mensual": [115, 123, 303, 349, 111],
                   "trimestral": [115, 123, 303, 349, 110],
                   "anual": [140, 180, 184, 200, 347, 390, 391, 190]}

        año = re.findall('Ejercicio([\s\S]+?)(202\d{1})', pdf_text)
        if len(año) > 0:
            ejercicio = año[0][-1]
        else:
            ejercicio = re.findall("(20\d{2})",impuesto)[0]

        #anual = re.findall(r'(>?Per[í|i]odo[\s\S]+?)(Anual)', pdf_text, re.IGNORECASE)




        # Declaraciones complementarias y sustitutivas


        nombre_documento = nombre[0:50]

        if modelo in modelos["anual"]:
            anual = re.findall(r'(>?Per[í|i]odo[\s\S]+?)(Anual)', pdf_text, re.IGNORECASE)
            if modelo == 200:
                periodo = "CIERRE"
                nombre_archivo = f"{modelo}_{ejercicio}{nombre_documento}.pdf"
            else:
                periodo = f"4º TRIM. {ejercicio}"
                nombre_archivo = f"{modelo}_{ejercicio}_4T_{nombre_documento}.pdf"

        else:
            mensual = re.findall(
                r"(>?Per[í|i]odo[\s\S]+?)(ENERO|FEBR.|MARZO|ABRIL|MAYO|JUN.|JUL.|AGO.|SET.|OCT.|NOV.|DIC.)", pdf_text)
            mensual_num = re.findall(f"(>?{ejercicio})\n(01|02|03|04|05|06|07|08|09|10|11|12)", pdf_text)
            mensual_texto = re.findall(
                "(Periodo\s)(.?)(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)",
                pdf_text, re.IGNORECASE)
            trimestral = re.findall('(TRIM\d{1})', pdf_text)

            if len(trimestral) > 0:
                trimestre = trimestral[0].replace("TRIM", "").strip()
                periodo = f"{trimestre}º TRIM. {ejercicio}"
                mes = f"{trimestre}T"
                nombre_archivo = f"{modelo}_{ejercicio}_{mes}_{nombre_documento}.pdf"

            elif len(mensual) > 0:
                month_list = {
                    'ENERO': 1,
                    'FEBR.': 2,
                    'MARZO': 3,
                    'ABRIL': 4,
                    'MAY0': 5,
                    'JUN.': 6,
                    'JUL.': 7,
                    'AGO.': 8,
                    'SEP.': 9,
                    'OCT.': 10,
                    'NOV.': 11,
                    'DIC.': 12
                }
                try:
                    mes = month_list[mensual[0][-1]]
                except:
                    mes = month_list[mensual[-1][-1]]
                trimestre = math.ceil(mes / 3)
                periodo = f"{trimestre}º TRIM. {ejercicio}"
                nombre_archivo = f"{modelo}_{ejercicio}_{mes}_{nombre_documento}.pdf"

            elif len(mensual_num) > 0:
                mes = mensual_num[0][-1]
                trimestre = math.ceil(mes / 3)
                periodo = f"{trimestre}º TRIM. {ejercicio}"
                nombre_archivo = f"{modelo}_{ejercicio}_{mes}_{nombre_documento}.pdf"

            elif len(mensual_texto) > 0:
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
                try:
                    mes = meses_dict[mensual_texto[0][-1].upper()]
                except:
                    mes = meses_dict[mensual_texto[-1][-1].upper()]
                trimestre = math.ceil(mes / 3)
                periodo = f"{trimestre}º TRIM. {ejercicio}"
                nombre_archivo = f"{modelo}_{ejercicio}_{mes}_{nombre_documento}.pdf"

        folder_path = f"Z:/Descargas/{nombre}_{nif}/{ejercicio}/IMPUESTOS/{periodo}/"
        Folder(folder_path)
        file.move(folder_path)

        #Si el archivo  existe
        if File(folder_path + nombre_archivo).exists:
              check = re.findall("(✔|✖)", pdf_text, re.IGNORECASE)
              if len(check) > 0:
                  if len(re.findall("sustitutiva", pdf_text, re.IGNORECASE)) > 0:
                      nombre_archivo= nombre_archivo.replace(".pdf","SUSTITUTIVA.pdf")
                      file.rename(nombre_archivo)
                  elif len(re.findall("complementaria", pdf_text, re.IGNORECASE)):
                      nombre_archivo = nombre_archivo.replace(".pdf","_COMPLEMENTARIA.pdf")
                      file.rename(nombre_archivo)
        else:
            file.rename(nombre_archivo)
        return (impuesto, modelo, periodo, file.path)
