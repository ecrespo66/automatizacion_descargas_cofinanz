import math
import re
import threading
import time
from datetime import datetime
from pywinauto import Desktop
from files_and_folders.files import File
from files_and_folders.folders import Folder
from files_and_folders.pdfs import PDF
from selenium.webdriver import Keys, ActionChains

from .constants import DOWNLOAD_FOLDER, COMMON_FOLDER
from .selectors import AppSelectors as AS


class App:
    def __init__(self, browser):
        self.browser = browser
        self.exception_event = threading.Event()
        self.exception = None


    def load_certificate(self):
        time.sleep(30)
        # Crea un objeto Desktop para interactuar con la interfaz de usuario de Windows
        try:
            desktop = Desktop(backend="uia")
            main_window = desktop.window(title="Seleccionar un certificado", top_level_only=False, found_index=0)
            main_window.wait('visible')
            main_window.set_focus()
            main_window.child_window(title="Aceptar", control_type="Button").click()
        except Exception as e:
            self.exception = e
            self.exception_event.set()


    def login(self):

        self.browser.open("https://www.ebizkaia.eus/es/profesional")
        self.browser.maximize_window()

        if self.browser.element_exists('xpath', AS.ACEPTAR_COOKIES.value):
            self.browser.find_element('xpath', AS.ACEPTAR_COOKIES.value).click()
        self.browser.wait_for_element('xpath', AS.MIS_GESTIONES.value, 120)
        self.browser.find_element('xpath', AS.MIS_GESTIONES.value).click()
        self.browser.wait_for_element('xpath', AS.MIS_PRESENTACIONES.value)
        self.browser.find_element('xpath', AS.MIS_PRESENTACIONES.value).click()
        self.browser.wait_for_element('xpath', AS.CERTIFICADOS_DIGITALES.value, 120)
        thread = threading.Thread(target=self.load_certificate, daemon=True)
        thread.start()
        self.browser.find_element('xpath', AS.CERTIFICADOS_DIGITALES.value).click()
        thread.join(timeout=60)


        # Check if an exception was set
        if self.exception_event.is_set():
            raise self.exception

    def find_client(self, nif):

        self.browser.wait_for_element('xpath', AS.INPUT_SELECTOR.value, 60)
        self.browser.find_element("xpath", AS.INPUT_SELECTOR.value).click()
        self.browser.find_element("xpath", AS.INPUT_SELECTOR.value).send_keys(Keys.COMMAND + "a")
        self.browser.find_element("xpath", AS.INPUT_SELECTOR.value).clear()
        self.browser.find_element("xpath", AS.INPUT_SELECTOR.value).send_keys(nif)
        CLIENT_SELECTOR = f"//span[contains(text(),'{nif}')]"

        try:
            self.browser.wait_for_element("xpath", CLIENT_SELECTOR, timeout=10)
            self.browser.find_element("xpath", CLIENT_SELECTOR).click()
            self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE.value, timeout=60)
        except:
            return False



    def descargar_documentos(self, i):
        self.browser.find_element('xpath',  f"//*[@id='form1:tablaPresentaciones:{i}:AccionPresentacion']").click()
        time.sleep(1)
        try:
            self.browser.wait_for_element("xpath", f"//a[@id='form1:tablaPresentaciones:{i}:justificante_']", 10)
        except:
            self.browser.find_element("xpath", AS.BUSCAR.value).click()
            time.sleep(1)
            self.browser.find_element('xpath', f"//*[@id='form1:tablaPresentaciones:{i}:AccionPresentacion']").click()
            self.browser.wait_for_element("xpath", f"//a[@id='form1:tablaPresentaciones:{i}:justificante_']", 10)

        self.browser.find_element('xpath', f"//a[@id='form1:tablaPresentaciones:{i}:justificante_']").click()
        time.sleep(3)
        self.browser.find_element('xpath', f"//tr[@data-ri='{i}']").click()
        self.browser.find_element('xpath', f"//tr[@data-ri='{i}']").click()


        return


    def filter_data(self, start_date, end_date):

        self.browser.wait_for_element_to_be_clickable("xpath", AS.CAMBIAR_BUSQUEDA.value, 30)
        self.browser.find_element('xpath', AS.CAMBIAR_BUSQUEDA.value).click()
        self.browser.wait_for_element("xpath", AS.FECHA_DESDE.value, 30)
        time.sleep(2)
        self.browser.find_element("xpath", AS.FECHA_DESDE.value).send_keys(start_date)

        self.browser.find_element("xpath", AS.FECHA_HASTA.value).send_keys(
            end_date)
        self.browser.find_element("xpath", AS.BUSCAR.value).click()

        self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE.value, timeout=60)
        time.sleep(5)
        tramites = int(self.browser.find_element('xpath', AS.EXPEDIENTES_ENCONTRADOS.value).text.split(" ")[0])

        if tramites > 0:
            return [*range(tramites)]
        else:
            return []



    def obtener_informacion_impuesto(self, tramite):
        self.browser.wait_for_element_to_be_clickable('xpath', AS.TRAMITES.value, 10)
        self.browser.find_elements('xpath', AS.TRAMITES.value)[tramite].click()
        self.browser.wait_for_element_to_be_clickable('xpath', AS.TRAMITACION.value, 10)
        self.browser.find_element("xpath", AS.TRAMITACION.value).click()

        impuesto = self.browser.find_element("xpath", AS.NOMBRE_IMPUESTO.value).text

        if "IRPF" in impuesto:
            modelo = "IRPF"
        else:
            modelo = self.browser.find_element("xpath", AS.MODELO_TEXTO.value).text
            match = re.findall(f"M[0-9]+", modelo)
            modelo = int(match[0].replace("M", ""))

        fecha = self.browser.find_element("xpath", AS.FECHA_APERTURA.value).text
        fecha_apertura = datetime.strptime(fecha, "%d/%m/%Y")

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
        return True



    def go_back(self):
        self.browser.find_element('xpath', AS.VOLVER.value).click()
        self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE.value, timeout=60)

    def save_file(self, file, nombre, nif, cod_cliente):

        pdf = PDF(file.path)
        pdf_text = pdf.read_pdf()
        periodo = ""

        #Buscamos en modelo en el documento
        modelo = re.findall(r"Modelo (\d{3})", pdf_text)
        if len(modelo) >0:
            modelo = int(modelo[0])
        else:
            raise NameError("No se localiza el modelo en el documento")

        if not nif in pdf_text:
            raise Exception("El nif No coincide con el documento")

        modelos = {"mensual": [111],
                   "mensual/trimestral":[115,123,303,349,216,309],
                   "trimestral": [130,110],
                   "anual": [190,140,180,184,200,220,390,347,232,296, 345]}


        #Buscamos en ejercicio en el documento
        año = re.findall(r'(Ejercicio|período)([\s\S]+?)(202\d{1})', pdf_text)
        if len(año) > 0:
            ejercicio = año[0][-1]
        else:
            ejercicio = re.findall(r"(20\d{2})", pdf_text)[0]


        #Si el modelo está entre los modelos anuales
        if modelo in modelos["anual"]:
            nombre_archivo = f"{nif} {nombre} {modelo} {ejercicio[-2:]}.pdf"

        #Si el modelo e mensual
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
            nombre_archivo = f"{nif} {nombre} {modelo} {mes} {ejercicio[-2:]}.pdf"

        #Si el modelo es trimestral
        elif modelo in modelos["trimestral"]:
            trimestral = re.findall(r'(TRIM\d{1})', pdf_text)
            if len(trimestral) > 0:
                trimestre = trimestral[0].replace("TRIM", "").strip()
                trimestre = f"{trimestre}º trimestre"
                nombre_archivo = f"{nif} {nombre} {modelo} {trimestre} {ejercicio[-2:]}.pdf"
            else:
                raise Exception("No se localiza el trimestre")

        elif modelo in modelos["mensual/trimestral"]:
            mensual = re.findall(
                r"(>?Per[í|i]odo[\s\S]+?)(ENERO|FEBR.|MARZO|ABRIL|MAYO|JUN.|JUL.|AGO.|SET.|OCT.|NOV.|DIC.)", pdf_text)

            mensual_num = re.findall(rf"(>?{ejercicio})\n(01|02|03|04|05|06|07|08|09|10|11|12)", pdf_text)
            mensual_texto = re.findall(
                r"(Periodo\s)(.?)(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)",
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
                    periodo = month_list[mensual[0][-1]]
                except:
                    periodo = month_list[mensual[-1][-1]]
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
                periodo = month_list[mensual_num[0][-1]]
            elif len(mensual_texto) > 0:
                try:
                    periodo = mensual_texto[0][-1]
                except:
                    periodo = mensual_texto[-1][-1]
            else:
                raise NameError("No se localiza el Periodo en el documento")

            nombre_archivo = f"{nif} {nombre} {modelo} {periodo} {ejercicio[-2:]}.pdf"


        else:
            raise NameError("El modelo no se encuentra en la lista de modelos")


        folder_path = DOWNLOAD_FOLDER + f"\\{cod_cliente}\\IMPUESTOS\\{ejercicio}"
        #Folder(folder_path)


        file.rename(nombre_archivo)
        Folder(COMMON_FOLDER)
        if not File(COMMON_FOLDER + nombre_archivo).exists:
            #file.move(folder_path)
            file.move(COMMON_FOLDER)
        #if not File(folder_path  +"\\" + nombre_archivo).exists:
        #    #file.move(folder_path)
        #    print(folder_path  +"\\" + nombre_archivo)
        return (modelo, periodo, file.path)
