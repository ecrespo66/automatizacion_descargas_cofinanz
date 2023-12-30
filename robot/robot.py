from datetime import datetime
from browser.chrome import ChromeBrowser
from dateutil.relativedelta import relativedelta
from files_and_folders.folders import Folder
from files_and_folders.pdfs import PDF
from robot_manager.base import Bot
import pyautogui
import pandas as pd
import time
from .flow import *
from .exceptions import *
from .utils import last_day_of_month


class Robot(Bot):
    """
    Robot class:
    ----------------
    Robot class - Inherits from Bot class.
    This Framework is design to test the Robot Funcionality
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs, disabled=True)

    @RobotFlow(Nodes.StartNode, children="get_client_data")
    def start(self):
        """
        start method
        ======================
        Start method is the first method to be executed.
        Use this method to execute the robot's initialization.
        Example:
            1. Initialize the robot's variables.
            2. Clean up the environment.
            3. Get the robot's data.
            4. Open Applications
        """
        # Transaction data example

        self.tempFolder = "C:\\Users\\administrador\\Documents\\temp"
        self.folder = Folder(self.tempFolder)
        self.folder.empty()

        self.browser = ChromeBrowser()
        self.browser.options.page_load_strategy = 'none'
        self.browser.set_download_folder(self.tempFolder)

        self.browser.open("https://www.ebizkaia.eus/es/profesional")

        self.browser.maximize_window()
        self.browser.wait_for_element('xpath', "//*[contains(text(),'Aceptar Todas')]")
        self.browser.find_element('xpath', "//a[contains(text(),'Aceptar Todas')]").click()
        self.browser.wait_for_element('xpath', "//*[contains(text(),'Mis gestiones')]")
        self.browser.find_element('xpath', "//*[contains(text(),'Mis gestiones')]").click()
        self.browser.wait_for_element('xpath', "//*[contains(text(),'Mis expedientes')]")
        self.browser.find_element('xpath', "//*[contains(text(),'Mis expedientes')]").click()
        self.browser.wait_for_element('xpath', "//*[contains(text(),'Certificados digitales')]", 20)
        self.browser.find_element('xpath', "//*[contains(text(),'Certificados digitales')]").click()

        time.sleep(5)
        pyautogui.press("enter")
        time.sleep(10)

        self.data = pd.read_excel("Z:\CLIENTES Y MAILS.xlsx")
        self.transaction_number = 0

    @RobotFlow(Nodes.ConditionNode, children={True: "get_client_documents", False: "end"}, condition=Conditions.has_data)
    def get_client_data(self, *args):
        """
        Get transaction data method
        ===========================
        Get transaction data method is the method that gets the data from the source.
        Use this method to get each transactional item and send it to the next method to be processed.
        Example usage:
            1. Get the data from the source.
            2. Send the data to the next method.
        """
        # self.log.trace("get_transaction_data")

        return self.data.iloc[0]

    @RobotFlow(Nodes.OperationNode, children="process_documents")
    def get_client_documents(self, *args):
        """
        Process data Method
        ======================
        Process data method is the method that processes the data gathered from the previous method.
        Use this method to process the data.
        Arguments:
            1. *args: Receives data from the previous method.
        Example usage:
            1. Process the data.
        """
        if len(args) > 0:
            item = args
            self.nif = item[0][0]
            self.log.debug(f"se va a procesar el {self.nif}")
            self.transaction_number = self.transaction_number + 1
        try:
            input_selector = "//input[@id='form1:inputSelectPoderdante_input']"
            self.browser.wait_for_element('xpath', input_selector, 30)
            self.browser.find_element("xpath", input_selector).click()
            self.browser.find_element("xpath", input_selector).clear()
            time.sleep(1)
            self.browser.find_element("xpath", input_selector).send_keys(self.nif)
            time.sleep(3)

            if self.browser.element_exists("xpath", f"//*[contains(text(),'{self.nif}')]"):
                self.browser.find_element("xpath", f"//*[contains(text(),'{self.nif}')]").click()
                self.browser.wait_for_element_to_disappear("xpath", "//*[contains(text(),'Cargando...')]", timeout=30)

            else:
                raise BusinessException(self, message=f"No se encuentra el usuario {self.nif}", next_action="set_transaction_status")

            # Filtrar expedientes por fecha
            prev_month = datetime.now() - relativedelta(months=1)
            start_date = f"1/{prev_month.month}/{prev_month.year}"
            end_date = f"{last_day_of_month(prev_month.year, prev_month.month)}/{prev_month.month}/{prev_month.year}"

            self.browser.wait_for_element_to_be_clickable("xpath", "//*[contains(text(),'Cambiar búsqueda')]", 30)
            time.sleep(5)
            self.browser.find_element('xpath', "//*[contains(text(),'Cambiar búsqueda')]").click()

            self.browser.wait_for_element("xpath", "//input[@id='form1:fechaAperturaExpedienteDesde_input']", 30)
            time.sleep(3)
            self.browser.find_element("xpath", "//input[@id='form1:fechaAperturaExpedienteDesde_input']").send_keys(
                start_date)

            self.browser.find_element("xpath", "//input[@id='form1:fechaAperturaExpedienteHasta_input']").send_keys(
                end_date)
            self.browser.find_element("xpath", "//button[@id='form1:botonBuscar']").click()

            self.browser.wait_for_element_to_disappear("xpath", "//*[contains(text(),'Cargando')]", timeout=60)
            time.sleep(3)

            # Si no encuentra el botón de trámite lanza una excepción al siguiente
            if not self.browser.element_exists('xpath', "//*[contains(text(),'Trámites')]"):
                raise BusinessException(self, message="No hay Trámites para el usuario", next_action="set_transaction_status")
            return self.browser.find_elements('xpath', "//*[contains(text(),'Trámites')]")

        except BusinessException as BE:
            self.log.business_exception(BE.message)

            self.data = self.data.drop(0)
            self.data.reset_index(drop=True, inplace=True)
            raise BE

        except Exception as e:
            self.log.system_exception(e)
            self.browser.get("https://ataria.ebizkaia.eus/es/mis-expedientes/")
            raise SystemException(self, message=e, next_action="retry")

    @RobotFlow(Nodes.ConditionNode, children={True: "download_document", False: "set_transaction_status"},
               condition=Conditions.has_data)
    def process_documents(self, *args):
        if args:
            tramites = args[0]
            return tramites
        else:
            return []

    @RobotFlow(Nodes.OperationNode, children="process_documents")
    def download_document(self, *args):
        try:
            tramites = args[0]
            tramite = tramites[0]
            tramite.click()
            self.browser.wait_for_element("xpath", "//*[contains(text(),'Documentación')]", 30)
            time.sleep(3)
            self.browser.find_element('xpath', "//*[contains(text(),'Documentación')]").click()

            self.browser.wait_for_element("xpath", "//*[contains(text(),'Descargar')]", 30)

            if self.browser.element_exists("xpath", "//*[contains(text(),'No hay resultados')]"):
                raise BusinessException(self, message="NO hay documentos para descargar", next_action="set_transaction_status")

            time.sleep(5)
            self.browser.find_elements('xpath', "//a[contains(@id,'form1:pestanias:j_idt')]")[3].click()
            time.sleep(10)

            if len(self.folder.file_list()) == 0:
                raise Exception("NO se ha descargado el documento")

            file = self.folder.file_list()[0]
            pdf = PDF(file.path)
            pdf_text = pdf.read_file()
            # Validamos el pdf
            if not self.nif in pdf_text:
                file.remove()
                raise BusinessException(self, message="El documento no corresponde al cliente", next_action="set_transaction_status")

            file.move(new_location="C:/Users/administrador/Documents/final_folder/")

            # Buscamos el tipo
            if "sustitutiva" in pdf_text:
                tipo = "sustitutiva"
            elif "complementaria" in pdf_text:
                tipo = "complementaria"
            else:
                tipo = "normal"

            self.browser.find_element('xpath', "//*[contains(text(),'Volver')]").click()

            self.browser.wait_for_element_to_disappear("xpath", "//*[contains(text(),'Cargando')]", timeout=60)
            tramites.pop(0)
            return tramites

        except BusinessException as BE:
            self.log.business_exception(BE.message)
            raise BE

        except Exception as e:
            self.log.system_exception("Error: Se va a reintentar la descarga del documento")
            self.browser.back()
            raise SystemException(self, message=e, next_action="retry")



    @RobotFlow(Nodes.OperationNode, children="get_client_data")
    def set_transaction_status(self, *args):
        # Remove Processed Item
        if len(args[0])>0:
            result = args[0]
        else:
            result = "OK"
        self.log.trace(result)
        self.data = self.data.drop(0)
        self.data.reset_index(drop=True, inplace=True)

    @RobotFlow(node=Nodes.EndNode)
    def end(self, *args):
        """
        Ends the workflow. Closes any open resources like the web browser
        """
        self.browser.close()
        # self.log.trace(f"end")
