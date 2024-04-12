import time
from datetime import datetime

import openpyxl
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
from email_activities.mails import Mail

class Robot(Bot):
    """
    Este robot se encarga de descargar los trámites pendientes en la web de la agencia tributaria de Vizcaya,
    Guardarlos en la ruta corresponmdiente y enviarselos a los clientes
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs, disabled=False)
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
            self.tempFolder = "Z:\\temp"
            self.folder = Folder(self.tempFolder)
            self.folder.empty(allow_root=True)
            #prev_month = datetime.now() - relativedelta(months=2)
            self.start_date = datetime.strptime(self.parameters.get('date-from'), '%Y-%m-%d').strftime('%d/%m/%Y') # #f"1/{prev_month.month}/{prev_month.year}" #
            self.end_date =  datetime.strptime(self.parameters.get('date-to'),  '%Y-%m-%d').strftime('%d/%m/%Y')  #f"{last_day_of_month(prev_month.year, prev_month.month +1)}/{prev_month.month+1}/{prev_month.year}"
            self.mail = Mail('envios@asesoriaheras.es', "Voz94497", 'asesoriaheras-es.mail.protection.outlook.com', 25,
                             'asesoriaheras-es.mail.protection.outlook.com', 993)
            self.log.trace(f"Se van a obtener los impuestos desde {self.start_date} hasta {self.end_date}")
            self.browser = ChromeBrowser(undetectable=True)
            self.browser.options.page_load_strategy = "normal"
            #self.browser.options.page_load_strategy = 'none'
            self.browser.options.add_experimental_option("prefs", {
                "download.prompt_for_download": False,  # Desactiva el diálogo de confirmación de descarga
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
                "download.default_directory": f"{self.tempFolder}",
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing_for_trusted_sources_enabled": False,
                "safebrowsing.enabled": False
            })
            self.app = App(self.browser)
            self.app.login()

            self.workbook_path = "Z:\CLIENTES Y MAILS.xlsx"
            self.data = pd.read_excel(self.workbook_path)
            self.transaction_number = 0
            self.wb = openpyxl.load_workbook(self.workbook_path)


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
            self.nif = args[0].iloc[0]
            self.name = args[0].iloc[1]
            self.downloaded_documents = []
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

            self.folder.empty()
            tax_info = self.app.obtener_informacion_impuesto(tramite)
            self.log.trace("Modelo: " + str(tax_info["modelo"]))
            lista_modelos = [115, 123, 130, 303, 349, 140, 180, 184, 200, 347, 390, 391, 111, 110, 190]
            if tax_info["modelo"] not in lista_modelos:
                raise BusinessException(self, message="El modelo no se encuentra en la lista de modelos", next_action="skip")

            if self.app.download_document() is not True:
                raise BusinessException(self, message="No hay documentos a descargar", next_action="skip")
            time.sleep(5)

            if len(self.folder.file_list(".pdf")) == 0:
                raise Exception("No se ha descargado el documento")

            file = self.folder.file_list(".pdf")[0]

            try:
                impuesto = self.app.save_file(file, self.name, self.nif, tax_info["modelo"], tax_info["impuesto"] )
            except Exception as e:
                self.log.system_exception(e)
                raise Exception(e)

            self.log.trace(impuesto[3])
            self.app.go_back()

            page = self.wb['IMPUESTOS']
            page.append([self.nif, self.name, impuesto[0], impuesto[1], impuesto[2], impuesto[3]])
            self.wb.save(self.workbook_path)
            self.folder.empty()
            tramites.pop(0)

            archivo = impuesto[3]
            self.downloaded_documents.append(archivo)
            return tramites

        except BusinessException as BE:
            self.log.business_exception(BE.message)
            tramites.pop(0)
            self.app.go_back()
            raise BE

        except Exception as e:
            self.log.system_exception(e)
            try:
                self.folder.empty(allow_root=True)
                self.app.go_back()
            except:
                raise SystemException(self, message=e, next_action="retry")

            raise SystemException(self, message=e, next_action="retry")

    @RobotFlow(Nodes.OperationNode, children="get_client_data")
    def set_transaction_status(self, *args):
        # Remove Processed Item
        if len(args[0]) > 0:
            result = args[0][0]
        else:
            result = "OK"
            self.log.trace(result)

            text = f"Estimado cliente:\nAdjunto se remite documentación contable PARA ARCHIVAR. Con la obligación de que sea guardada en forma impresa o en este formato (serecomienda las dos), para posible presentación ante: Organismos, Inspecciones, Bancos, etc.\nAtentamente."
            #self.mail.send(["alicia@asesoriaheras.es", "arantza@asesoriaheras.es"], "ENVIO IMPUESTOS", text=text, files= self.downloaded_documents)

            # Selecciona la hoja en la que quieres buscar y actualizar
        hoja = self.wb['CLIENTES']
        # Dato que estás buscando
        dato_a_buscar = self.nif
        # Busca el dato en la columna A y obtén la fila
        fila = None
        for fila_actual in range(1, hoja.max_row + 1):
            if hoja.cell(row=fila_actual, column=1).value == dato_a_buscar:
                fila = fila_actual
                break
        # Si se encuentra el dato, actualiza la celda correspondiente en la columna D
        if fila is not None:
            hoja.cell(row=fila, column=7).value = result
            hoja.cell(row=fila, column=8).value = datetime.today().strftime("%d-%m-%y")
        # Guarda los cambios en el archivo
        self.wb.save("Z:\CLIENTES Y MAILS.xlsx")
        self.wb.close()

        self.data = self.data.drop(0)
        self.data.reset_index(drop=True, inplace=True)

    @RobotFlow(node=Nodes.EndNode)
    def end(self, *args):
        """
        Este método cierra el Navegador web.
        """
        self.browser.close()
        self.log.trace(f"end")
