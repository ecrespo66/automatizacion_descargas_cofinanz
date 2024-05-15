#Robot

    Este robot se encarga de descargar los trámites pendientes en la web de la agencia tributaria de Vizcaya,
    Guardarlos en la ruta corresponmdiente y enviarselos a los clientes
    
# FLOW NODES
## start
 
        En este método se inicializa el robot, se definen las variables globales como rutas de descargas,
        datos de entrada y otras variables que se utilizarán durante el proceso y se inicia sesión en la página web de la agencia tributaria de Vizcaya.

        En caso de excepción, este nódo se reintentara 3 veces
        
## get_client_data
 
        A partir de la variable data (self.data) creada en el método anterior,
        se gestionan las transacciones una a una para procesarla por los siguiente métodos:
            1. Si existen transacciones pendientes de procesar: se llama al método "get_cliente_documents",
            2. En caso contrario termina el proceso método "end"
        
## get_client_documents
 
        En este método se busca al cliente y se filtran los expediente del mes correspondiente.
        Recibe como argumento una la información del cliente.
        Devuelve una lista con los trámites disponibles para descargar.

        Exceciones:
            1. Excepciones de Negocio:
                1.1 No se encuentra al usuario -> next_action: "set_transaction_status"
                1.2 No hay trámites para el usuario -> next_action: "set_transaction_status"
            2. Excepciones de Sistema:
                Cualquier excepcion no controlada -> next_action: "retry"

        
## process_documents
 
        Se evalúa si quedan trámites disponibles del cliente para descargar, en caso de que existan,
        Se procederá a llamar al nodo de "download_document.
        En caso contrario, se gestionará la transacción en el nodo "set_transaction_status"
        
## download_document
 
        Este método recibe como argumento el trámite que se tiene que procesar.
        Descarga el documento y lee la información de este.

        Excepciones:
            1. Negocio: No hay documentos para descargar -> next_action : "set_transaction_status"
            2. Sistema: No se ha descargadi el documento -> next_action: "rety"
        
## set_transaction_status
## end
 
        Ends the workflow. Closes any open resources like the web browser
        
