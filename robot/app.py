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
import pdfplumber


class App:
    def __init__(self, browser):
        self.browser = browser
        self.exception_event = threading.Event()
        self.exception = None

    def read_form(self,pdf_path):
        texto_completo = ""

        with pdfplumber.open(pdf_path) as pdf:
            for pagina in pdf.pages:
                texto_completo += pagina.extract_text() + "\n"

        return texto_completo


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
        self.browser.find_element("xpath", AS.SEARCH_BUTTON.value).click()
        CLIENT_SELECTOR = f"//span[contains(text(),'{nif}')]"
        time.sleep(10)
        if self.browser.find_element("xpath", "//input[@id='form1:nombrePoderdante']").get_property("value") != "":
            self.browser.find_element("xpath", AS.FILTER_SELECTOR.value).click()
            self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE.value, timeout=120)
        else:
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


        self.browser.wait_for_element_to_be_clickable("xpath", AS.CAMBIAR_BUSQUEDA.value, 120)
        self.browser.find_element('xpath', AS.CAMBIAR_BUSQUEDA.value).click()
        self.browser.wait_for_element("xpath", AS.FECHA_DESDE.value, 120)
        self.browser.find_element("xpath", AS.FECHA_DESDE.value).send_keys(
            start_date)


        self.browser.find_element("xpath", AS.FECHA_HASTA.value).send_keys(
            end_date)

        if self.browser.find_element("xpath", AS.FECHA_DESDE.value).get_property("value") != start_date or self.browser.find_element("xpath", AS.FECHA_HASTA.value).get_property("value") != end_date:
            raise Exception("No se han filtrado bien bien las fechas")

        self.browser.find_element("xpath", AS.BUSCAR.value).click()

        self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE.value, timeout=60)
        time.sleep(5)

        if self.browser.element_exists('xpath', AS.EXPEDIENTES_ENCONTRADOS.value):
            try:
                tramites = int(self.browser.find_element('xpath',"//*[contains(text(),'presentaciones encontradas')]").text.replace('presentaciones encontradas',"").strip())
                #self.browser.find_elements('xpath', AS.TRAMITES.value)
            except:
                tramites = 1
            
            #tramites = self.browser.find_elements('xpath', AS.TRAMITES.value)
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

        pdf_text = self.read_form(file.path)
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
                   "anual": [190,193,140,180,184,200,220,390,347,232,296,203, 345]}


        #Buscamos en ejercicio en el documento
        ejercicio = None
        año = re.findall(r'(Ejercicio|período|anual)[\s\S]+?(\b202\d{1})', pdf_text)
        if len(año) > 0:
            for a in año:
                if a[0] == "Ejercicio":
                    ejercicio = a[-1]
            if not ejercicio:
                ejercicio = año[-1][-1]
        else:
            ejercicio = re.findall(r"(20\d{2})", pdf_text)[0]


        #Si el modelo está entre los modelos anuales
        if modelo in modelos["anual"]:
            nombre_archivo = f"{nif} {nombre} {modelo} {ejercicio[-2:]}.pdf"

        #Si el modelo e mensual
        elif modelo in modelos["mensual"]:
            mensual = re.findall(
                r">?Per[í|i]odo[\s\S]+?(ENERO|FEBR.|MARZO|ABRIL|MAYO|JUN.|JUL.|AGO.|SET.|OCT.|NOV.|DIC.)\n", pdf_text)

            mensual_num = re.findall(rf">?{ejercicio}\n(01|02|03|04|05|06|07|08|09|10|11|12)", pdf_text)
            mensual_texto = re.findall(
                r">?Per[í|i]odo[\s\S]+?(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)",
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
                    mes = month_list[mensual[0]]
                except:
                    mes = month_list[mensual[-1]]
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
                mes = month_list[mensual_num[0]]

            elif len(mensual_texto) > 0:
                try:
                    mes = mensual_texto[0]
                except:
                    mes = mensual_texto[-1]
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
                r">?Per[í|i]odo[\s\S]+?(ENERO|FEBR.|MARZO|ABRIL|MAYO|JUN.|JUL.|AGO.|SET.|OCT.|NOV.|DIC.)\W", pdf_text)

            mensual_num = re.findall(rf">?{ejercicio}\n(01|02|03|04|05|06|07|08|09|10|11|12)", pdf_text)
            mensual_texto = re.findall(
                r"Per[í|i]odo[\s\S]+?(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)",
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

            nombre_archivo = f"{nif} {nombre} {modelo} {periodo} {ejercicio[-2:]}.pdf"


        else:
            raise NameError(f"El modelo {modelo} no se encuentra en la lista.")


        folder_path = DOWNLOAD_FOLDER + f"\\{cod_cliente}\\IMPUESTOS\\{ejercicio}"
        folder = Folder(folder_path)

        complementaria = re.findall(r"(complementaria|01) (✔|✖)", pdf_text)
        sustitutiva = re.findall(r"(sustitutiva|01) (✔|✖)", pdf_text)

        if len(complementaria) > 0:
            nombre_archivo = nombre_archivo.replace(".pdf", "_complementaria.pdf")
        elif len(sustitutiva)>0:
            nombre_archivo = nombre_archivo.replace(".pdf", "_sustitutiva.pdf")

        file.rename(nombre_archivo)
        Folder(COMMON_FOLDER)
        if not File(COMMON_FOLDER + nombre_archivo).exists:
            file.move(COMMON_FOLDER)
        if not File(folder_path  +"\\" + nombre_archivo).exists:
            file.copy(new_location= folder_path)
        #    print(folder_path  +"\\" + nombre_archivo)
        file.path = folder_path + "\\" +  nombre_archivo
        return (modelo, periodo, file.path)
