import time
import pyautogui
from files_and_folders.pdfs import PDF
from .selectors import AppSelectors as AS


class App:
    def __init__(self, browser):
        self.browser = browser

    def load_certificate(self):

        self.browser.open("https://www.ebizkaia.eus/es/profesional")
        self.browser.maximize_window()
        if self.browser.element_exists('xpath', AS.ACEPTAR_COOKIES, 10):
            self.browser.find_element('xpath', AS.ACEPTAR_COOKIES).click()
        self.browser.wait_for_element('xpath', AS.MIS_GESTIONES)
        self.browser.find_element('xpath', AS.MIS_GESTIONES).click()
        self.browser.wait_for_element('xpath', AS.MIS_EXPEDIENTES)
        self.browser.find_element('xpath', AS.MIS_EXPEDIENTES).click()
        self.browser.wait_for_element('xpath', AS.CERTIFICADOS_DIGITALES, 20)
        self.browser.find_element('xpath', AS.CERTIFICADOS_DIGITALES).click()
        time.sleep(5)
        pyautogui.press("enter")
        self.browser.wait_for_element("xpath", AS.CHECK_LOGIN, 60)

    def find_client(self, nif):
        self.browser.wait_for_element('xpath', AS.INPUT_SELECTOR, 60)
        self.browser.find_element("xpath", AS.INPUT_SELECTOR).click()
        self.browser.find_element("xpath", AS.INPUT_SELECTOR).clear()
        self.browser.find_element("xpath", AS.INPUT_SELECTOR).send_keys(nif)

        AS.CLIENT_SELECTOR = AS.get_client(nif)
        if self.browser.element_exists("xpath", AS.CLIENT_SELECTOR, 10):
            self.browser.find_element("xpath", AS.CLIENT_SELECTOR).click()
            self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE, timeout=60)
        else:
            return False

    def filter_data(self, start_date, end_date):

        self.browser.wait_for_element_to_be_clickable("xpath", AS.CAMBIAR_BUSQUEDA, 30)
        self.browser.find_element('xpath', AS.CAMBIAR_BUSQUEDA).click()
        self.browser.wait_for_element("xpath", AS.FECHA_DESDE, 30)
        self.browser.find_element("xpath", AS.FECHA_DESDE).send_keys(
            start_date)

        self.browser.find_element("xpath", AS.FECHA_HASTA).send_keys(
            end_date)
        self.browser.find_element("xpath", AS.BUSCAR).click()

        self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE, timeout=60)
        time.sleep(5)
        if self.browser.element_exists('xpath', AS.EXPEDIENTES_ENCONTRADOS, 10):
            tramites = self.browser.find_elements('xpath', AS.TRAMITES)
            return [*range(len(tramites))]
        else:
            return []

    def download_document(self, tramite):
        self.browser.wait_for_element_to_be_clickable('xpath',AS.TRAMITES, 10)
        self.browser.find_elements('xpath', AS.TRAMITES)[tramite].click()
        self.browser.wait_for_element("xpath",AS.DOCUMENTACION, 30)
        self.browser.find_element('xpath', AS.DOCUMENTACION).click()
        self.browser.wait_for_element("xpath", AS.DESCARGAR, 30)
        if self.browser.element_exists("xpath", AS.NO_RESULTADOS, 10):
            return 'No hay resultados'
        self.browser.find_elements('xpath', AS.BOTON_DESCARGA)[3].click()

    def go_back(self):
        self.browser.find_element('xpath', AS.VOLVER).click()
        self.browser.wait_for_element_to_disappear("xpath", AS.LOADING_PAGE, timeout=60)

    def read_file(self, file):

        pdf = PDF(file.path)
        pdf_text = pdf.read_file()
        # Validamos el pdf
        if not self.nif in pdf_text:
            file.remove()
            False

        file.move(new_location="C:/Users/administrador/Documents/final_folder/")

        # Buscamos el tipo
        if "sustitutiva" in pdf_text:
            tipo = "sustitutiva"
        elif "complementaria" in pdf_text:
            tipo = "complementaria"
        else:
            tipo = "normal"
