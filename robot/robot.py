import time
from datetime import datetime
from browser.chrome import ChromeBrowser
from dateutil.relativedelta import relativedelta
from files_and_folders.folders import Folder
from openpyxl.reader.excel import load_workbook
from robot_manager.base import Bot
import pandas as pd
from openpyxl.workbook import Workbook

from robot.app import App
from .flow import *
from .exceptions import *
from .utils import last_day_of_month


class Robot(Bot):
    """
    Este robot se encarga de descargar los trámites pendientes en la web de la agencia tributaria de Vizcaya,
    Guardarlos en la ruta corresponmdiente y enviarselos a los clientes
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs, disabled=True)
        self.transaction_number = None
        self.data = None
        self.app = None
        self.browser = None
        self.end_date = None
        self.start_date = None
        self.folder = None
        self.tempFolder = None
        self.nif = None

    @RobotFlow(Nodes.StartNode, children="get_client_data")
    def start(self):
        """
        En este método se inicializa el robot, se definen las variables globales como rutas de descargas,
        datos de entrada y otras variables que se utilizarán durante el proceso y se inicia sesión en la página web de la agencia tributaria de Vizcaya.

        Excepciones:
            1. Excepciones de Sistema:
                1.1 Cualquier excepción -> next_action: "retry"
        """

        try:
            self.tempFolder = "C:\\Users\\administrador\\Documents\\temp"
            self.folder = Folder(self.tempFolder)
            self.folder.empty()

            prev_month = datetime.now() - relativedelta(months=1)
            self.start_date = f"1/{prev_month.month}/{prev_month.year}"
            self.end_date = f"{last_day_of_month(prev_month.year, prev_month.month)}/{prev_month.month}/{prev_month.year}"

            self.browser = ChromeBrowser(undetectable=True)
            self.browser.options.page_load_strategy = "normal"
            #self.browser.options.page_load_strategy = 'none'
            self.browser.set_download_folder(self.tempFolder)
            self.app = App(self.browser)
            self.app.login()

            self.data = pd.read_excel("Z:\CLIENTES Y MAILS.xlsx")
            self.workbook_path = 'Z:\Descargas\clientes_impuestos.xlsx'
            self.transaction_number = 0


            self.wb = Workbook()
            page = self.wb.active
            page.title = 'documentos'
            page.append(['cif', 'Nombre', 'Impuesto', 'Modelo','Periodo', "Archivo"])  # write the headers to the first line
            self.wb.save(self.workbook_path)


        except Exception as e:
            self.browser.close()
            self.log.system_exception(e)
            raise SystemException(self, message=e, next_action="retry")

    @RobotFlow(Nodes.ConditionNode, children={True: "get_client_documents", False: "end"},
               condition=Conditions.has_data)
    def get_client_data(self, *args):
        """
        A partir de la variable data (self.data) creada en el método anterior,
        se gestionan las transacciones una a una para procesarla por los siguiente métodos:
            1. Si existen transacciones pendientes de procesar: se llama al método "get_cliente_documents",
            2. En caso contrario termina el proceso método "end"
        """
        if self.data.empty:
            return []
        return self.data.iloc[0]

    @RobotFlow(Nodes.OperationNode, children="process_documents")
    def get_client_documents(self, *args):
        """
        En este método se busca al cliente y se filtran los expediente del mes correspondiente.
        Recibe como argumento una la información del cliente.
        Devuelve una lista con los trámites disponibles para descargar.

        Exceciones:
            1. Excepciones de Negocio:
                1.1 No se encuentra al usuario -> next_action: "set_transaction_status"
                1.2 No hay trámites para el usuario -> next_action: "set_transaction_status"
            2. Excepciones de Sistema:
                Cualquier excepcion no controlada -> next_action: "retry"

        """
        try:
            self.nif = args[0][0]
            self.name = args[0][1]
            self.log.debug(f"se va a procesar el {self.nif}")
            self.transaction_number = self.transaction_number + 1

            if self.app.find_client(self.nif) is False:
                message = f"No se encuentra el usuario {self.nif}"
                raise BusinessException(self, message=message, next_action="set_transaction_status")
            time.sleep(10)
            tramites = self.app.filter_data(self.start_date, self.end_date)
            if len(tramites) == 0:
                message = "No hay tramites para el usuario"
                raise BusinessException(self, message=message, next_action="set_transaction_status")
            return tramites

        except BusinessException as BE:
            self.log.business_exception(BE.message)
            raise BE
        except Exception as e:
            self.log.system_exception("Error al obtener los documentos del cliente: Reintentando")
            self.browser.get("https://ataria.ebizkaia.eus/es/mis-expedientes/")
            raise SystemException(self, message=e, next_action="retry")

    @RobotFlow(Nodes.ConditionNode, children={True: "download_document", False: "set_transaction_status"},
               condition=Conditions.has_data)
    def process_documents(self, *args):
        """
        Se evalúa si quedan trámites disponibles del cliente para descargar, en caso de que existan,
        Se procederá a llamar al nodo de "download_document.
        En caso contrario, se gestionará la transacción en el nodo "set_transaction_status"
        """
        if args:
            tramites = args[0]
            return tramites
        else:
            return []

    @RobotFlow(Nodes.OperationNode, children="process_documents")
    def download_document(self, *args):
        """
        Este método recibe como argumento el trámite que se tiene que procesar.
        Descarga el documento y lee la información de este.

        Excepciones:
            1. Negocio: No hay documentos para descargar -> next_action : "set_transaction_status"
            2. Sistema: No se ha descargadi el documento -> next_action: "rety"
        """
        try:
            tramites = args[0]
            tramite = tramites[0]

            check_download = self.app.download_document(tramite)

            if check_download is not True:
                raise BusinessException(self, message=check_download, next_action="skip")
            time.sleep(5)
            if len(self.folder.file_list()) == 0:
                raise Exception("No se ha descargado el documento")
            tramites.pop(0)

            file = self.folder.file_list()[0]
            impuesto = self.app.save_file(file, self.name, self.nif)
            self.app.go_back()

            page = self.wb.active
            page.append([self.nif, self.name, impuesto[0], impuesto[1], impuesto[2], impuesto[3]])
            self.wb.save(self.workbook_path)
            self.folder.empty()
            return tramites

        except BusinessException as BE:
            self.log.business_exception(BE.message)
            raise BE

        except Exception as e:
            self.log.system_exception("Error: Se va a reintentar la descarga del documento")
            try:
                self.folder.empty()
                self.app.go_back()
            except:
                raise SystemException(self, message=e, next_action="retry")

            raise SystemException(self, message=e, next_action="retry")

    @RobotFlow(Nodes.OperationNode, children="get_client_data")
    def set_transaction_status(self, *args):
        # Remove Processed Item
        if len(args[0]) > 0:
            result = args[0][0]
            page = self.wb.active
            page.append([self.nif, self.name, "#N/A", "#N/A", "#N/A", result])
            self.wb.save(self.workbook_path)
        else:
            result = "OK"
            self.log.trace(result)
        self.data = self.data.drop(0)
        self.data.reset_index(drop=True, inplace=True)

    @RobotFlow(node=Nodes.EndNode)
    def end(self, *args):
        """
        Este método cierra el Navegador web.
        """
        self.browser.close()
        self.log.trace(f"end")
