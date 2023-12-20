from datetime import datetime

from browser.chrome import ChromeBrowser
from dateutil.relativedelta import relativedelta
from files_and_folders.folders import Folder
from files_and_folders.pdfs import PDF
from robot_manager.base import Bot
from robot_manager.flow import RobotFlow
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

    @RobotFlow(Nodes.StartNode)
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
        self.tempFolder = "C:\\Users\\administrador\\PycharmProjects\\Robot-framework\\temp"
        self.folder = Folder(self.tempFolder)
        self.folder.empty()

        self.browser = ChromeBrowser(undetectable=True)
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
        self.browser.wait_for_element('xpath', "//*[contains(text(),'Certificados digitales')]",20)
        self.browser.find_element('xpath', "//*[contains(text(),'Certificados digitales')]").click()

        time.sleep(5)
        pyautogui.press("enter")
        time.sleep(1)

        self.data = pd.read_excel("Z:\CLIENTES Y MAILS.xlsx")


    @RobotFlow(Nodes.ConditionNode, parents=["process_data"], condition=Conditions.has_data)
    def get_transaction_data(self, *args):
        """
        Get transaction data method
        ===========================
        Get transaction data method is the method that gets the data from the source.
        Use this method to get each transactional item and send it to the next method to be processed.
        Example usage:
            1. Get the data from the source.
            2. Send the data to the next method.
        """
        #self.log.trace("get_transaction_data")

        return self.data.iloc[0]

    @RobotFlow(Nodes.OnTrue, parents=["get_transaction_data"])
    def process_data(self, *args):
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

        item = args[0]
        nif = item[0]


        input_selector = "//input[@id='form1:inputSelectPoderdante_input']"
        time.sleep(10)
        self.browser.wait_for_element('xpath', input_selector,30)
        self.browser.find_element("xpath", input_selector).click()
        self.browser.find_element("xpath", input_selector).clear()
        time.sleep(1)
        self.browser.find_element("xpath",input_selector).send_keys(nif)
        #self.browser.wait_for_element('xpath', f"//*[contains(text(),'{nif}')]")
        time.sleep(3)
        if self.browser.element_exists("xpath", f"//*[contains(text(),'{nif}')]"):
            self.browser.find_element("xpath", f"//*[contains(text(),'{nif}')]").click()
            self.browser.wait_for_element_to_disappear("xpath", "//*[contains(text(),'Cargando...')]", timeout=30)
        else:
            self.data = self.data.drop(0)
            self.data.reset_index(drop=True, inplace=True)
            raise BusinessException(self, message=f"No se encuentra el usuario {nif}", next_action= "skip")

        prev_month = datetime.now() - relativedelta(months=1)
        start_date = f"1/{prev_month.month}/{prev_month.year}"
        end_date = f"{last_day_of_month(prev_month.year, prev_month.month)}/{prev_month.month}/{prev_month.year}"
        #Filtrar expedientes por fecha

        self.browser.wait_for_element_to_be_clickable("xpath", "//*[contains(text(),'Cambiar búsqueda')]", 30)
        time.sleep(5)
        self.browser.find_element('xpath', "//*[contains(text(),'Cambiar búsqueda')]").click()

        self.browser.wait_for_element("xpath","//input[@id='form1:fechaAperturaExpedienteDesde_input']", 30)
        time.sleep(3)
        self.browser.find_element("xpath", "//input[@id='form1:fechaAperturaExpedienteDesde_input']").send_keys(start_date)

        self.browser.find_element("xpath", "//input[@id='form1:fechaAperturaExpedienteHasta_input']").send_keys(end_date)
        self.browser.find_element("xpath", "//button[@id='form1:botonBuscar']").click()

        self.browser.wait_for_element("xpath", "//*[contains(text(),'Trámites')]", 30)
        time.sleep(3)
        #Si no encuentra el botón de trámite pasa al siguiente
        if not self.browser.element_exists('xpath', "//*[contains(text(),'Trámites')]"):
            self.data = self.data.drop(0)
            self.data.reset_index(drop=True, inplace=True)
            raise BusinessException(self, message="No hay Trámites para el usuario", next_action="skip")

        self.browser.find_element('xpath', "//*[contains(text(),'Trámites')]").click()

        self.browser.wait_for_element("xpath", "//*[contains(text(),'Documentación')]", 30)
        time.sleep(3)
        self.browser.find_element('xpath', "//*[contains(text(),'Documentación')]").click()

        self.browser.wait_for_element("xpath", "//*[contains(text(),'Descargar')]", 30)
        time.sleep(3)

        self.browser.find_elements('xpath', "//a[contains(@id,'form1:pestanias:j_idt')]")[3].click()
        time.sleep(3)

        #TODO lógica de guardado de ficheros


        file = self.folder.file_list()[0]
        pdf = PDF(file.path)
        pdf_text = ""
        for page in range(0,pdf.pages):
            pdf_text = pdf_text + pdf.read_page(page)
        self.folder.empty()
        #Validamos el pdf
        if not nif in pdf_text:
            raise BusinessException(self, message="El documento no corresponde al cliente", next_action="skip")


        #Buscamos el tipo
        if "sustitutiva" in pdf_text:
            tipo = "sustitutiva"
        elif "complementaria" in pdf_text:
            tipo = "complementaria"
        else:
            tipo = "normal"



        self.browser.find_element('xpath', "//*[contains(text(),'Volver')]").click()
        # Remove Processed Item
        self.data = self.data.drop(0)
        self.data.reset_index(drop=True, inplace=True)
        #self.log.trace(f"process_transaction_data for element {item}")

    @RobotFlow(node=Nodes.OnFalse, parents=["get_transaction_data"])
    def finish_process(self, *args):
        """
        Finish the workflow.
        Saves final changes to the Excel file.
        Sends output to user
        """
        #self.log.trace(f"finish_process")

    @RobotFlow(node=Nodes.EndNode, parents=["finish_process"])
    def end(self, *args):
        """
        Ends the workflow. Closes any open resources like the web browser
        """
        #self.log.trace(f"end")
