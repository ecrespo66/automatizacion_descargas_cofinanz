import math
import re
import threading
import time
from datetime import datetime

import pyautogui
from files_and_folders.folders import Folder
from files_and_folders.pdfs import PDF
from ibott_cv.screen_activities import Screen

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

    def download_document(self, tramite):

        self.browser.wait_for_element_to_be_clickable('xpath', AS.TRAMITES.value, 10)
        self.browser.find_elements('xpath', AS.TRAMITES.value)[tramite].click()
        self.browser.wait_for_element("xpath", AS.DOCUMENTACION.value, 30)
        self.browser.find_element('xpath', AS.DOCUMENTACION.value).click()
        self.browser.wait_for_element("xpath", AS.DESCARGAR.value, 30)
        if self.browser.element_exists("xpath", AS.NO_RESULTADOS.value):
            return 'No hay resultados'
        self.browser.find_elements('xpath', AS.BOTON_DESCARGA.value)[3].click()
        return True

    def go_back(self):
        self.browser.find_element('xpath', AS.VOLVER.value).click()
        self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE.value, timeout=60)

    def save_file(self, file, nombre, nif):

        self.browser.find_element("xpath", AS.TRAMITACION.value).click()

        impuesto = self.browser.find_element("xpath", AS.NOMBRE_IMPUESTO.value).text
        modelo = self.browser.find_element("xpath", AS.MODELO_TEXTO.value).text
        fecha = self.browser.find_element("xpath", AS.FECHA_APERTURA.value).text
        fecha_apertura = datetime.strptime(fecha, "%d/%m/%Y")
        match = re.findall("M[0-9]+", modelo)

        if len(match) > 0:
            modelo = match[0]
        else:
            modelo = re.findall("([A-Z]{1}[0-9]{8}|[0-9]+[A-Z]{1})(.*?)([0-9]{4})", impuesto)[0][1]

        ejercicio = fecha_apertura.year

        mes = fecha_apertura.month
        trimestre = math.ceil(mes / 3)

        if "anual" in impuesto:
            periodo = "CIERRE"
        else:
            periodo = f"{trimestre}º TRIM. {ejercicio}"

        pdf = PDF(file.path)
        pdf_text = pdf.read_file()
        # Validamos el pdf
        """
        if not self.nif in pdf_text:
            file.remove()
            False
        """
        # Buscamos el tipo
        if "sustitutiva" in pdf_text:
            tipo = "sustitutiva"
        elif "complementaria" in pdf_text:
            tipo = "complementaria"
        else:
            tipo = "normal"

        nombre_archivo = f"{modelo}_{ejercicio}_{mes}_{nombre}.pdf"
        # new_file_path = f"Y:/{nombre}_{nif}/{ejercicio}/IMPUESTOS/{periodo}/{nombre_archivo}"

        folder_path = f"Z:/Descargas/{nombre}_{nif}/{ejercicio}/IMPUESTOS/{periodo}/"
        Folder(folder_path)

        file.move(folder_path)

        file.rename(nombre_archivo)

        return (impuesto, modelo, periodo, file.path)
