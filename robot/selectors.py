from enum import Enum


class AppSelectors(Enum):
    FECHA_APERTURA = "//*[@id='form1:fechaAperturaExpediente']"
    TRAMITACION = "//*[text()='Tramitación']"
    MODELO_TEXTO = "//li[contains(text(), 'Presentación de declaración')]"
    NOMBRE_IMPUESTO = "//*[@id='form1:labeltituloEs']"
    ACEPTAR_COOKIES = "//*[contains(text(),'Aceptar Todas')]"
    MIS_GESTIONES = "//*[contains(text(),'Mis gestiones')]"
    MIS_EXPEDIENTES =  "//*[contains(text(),'Mis expedientes')]"
    CERTIFICADOS_DIGITALES = "//*[contains(text(),'Certificados digitales')]"
    CHECK_LOGIN = "//*[contains(text(),'HERAS CUADRADO, PEDRO')]"
    INPUT_SELECTOR = "//input[@id='form1:inputSelectPoderdante_input']"
    CLIENT_SELECTOR = None
    LOADING_PAGE = "//*[contains(text(),'Cargando...')]"
    CAMBIAR_BUSQUEDA = "//*[contains(text(),'Cambiar búsqueda')]"
    FECHA_DESDE = "//input[@id='form1:fechaAperturaExpedienteDesde_input']"
    FECHA_HASTA = "//input[@id='form1:fechaAperturaExpedienteHasta_input']"
    BUSCAR =  "//button[@id='form1:botonBuscar']"
    EXPEDIENTES_ENCONTRADOS =  "//*[contains(text(),'expedientes encontrados')]"
    TRAMITES = "//*[contains(text(),'Trámites')]"
    DOCUMENTACION =  "//*[contains(text(),'Documentación')]"
    DESCARGAR = "//*[contains(text(),'Descargar')]"
    NO_RESULTADOS = "//*[contains(text(),'No hay resultados')]"
    BOTON_DESCARGA = "//a[contains(@id,'form1:pestanias:j_idt')]"
    VOLVER = "//*[contains(text(),'Volver')]"


