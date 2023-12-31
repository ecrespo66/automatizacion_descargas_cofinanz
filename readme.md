#Robot

    Este robot se encarga de descargar los tr�mites pendientes en la web de la agencia tributaria de Vizcaya,
    Guardarlos en la ruta corresponmdiente y enviarselos a los clientes
    

# FLOW CHART
```mermaid
flowchart LR
0((start))
1{get_client_data}
2[get_client_documents]
3{process_documents}
4[download_document]
5[set_transaction_status]
6([end])
0-->1
1-->|True|2
1-->|False|6
2-->3
3-->|True|4
3-->|False|5
4-->3
5-->1
```
# FLOW NODES
## start
 
        En este m�todo se inicializa el robot, se definen las variables globales como rutas de descargas,
        datos de entrada y otras variables que se utilizar�n durante el proceso y se inicia sesi�n en la p�gina web de la agencia tributaria de Vizcaya.

        En caso de excepci�n, este n�do se reintentara 3 veces
        
## get_client_data
 
        A partir de la variable data (self.data) creada en el m�todo anterior,
        se gestionan las transacciones una a una para procesarla por los siguiente m�todos:
            1. Si existen transacciones pendientes de procesar: se llama al m�todo "get_cliente_documents",
            2. En caso contrario termina el proceso m�todo "end"
        
## get_client_documents
 
        En este m�todo se busca al cliente y se filtran los expediente del mes correspondiente.
        Recibe como argumento una la informaci�n del cliente.
        Devuelve una lista con los tr�mites disponibles para descargar.

        Exceciones:
            1. Excepciones de Negocio:
                1.1 No se encuentra al usuario -> next_action: "set_transaction_status"
                1.2 No hay tr�mites para el usuario -> next_action: "set_transaction_status"
            2. Excepciones de Sistema:
                Cualquier excepcion no controlada -> next_action: "retry"

        
## process_documents
 
        Se eval�a si quedan tr�mites disponibles del cliente para descargar, en caso de que existan,
        Se proceder� a llamar al nodo de "download_document.
        En caso contrario, se gestionar� la transacci�n en el nodo "set_transaction_status"
        
## download_document
 
        Este m�todo recibe como argumento el tr�mite que se tiene que procesar.
        Descarga el documento y lee la informaci�n de este.

        Excepciones:
            1. Negocio: No hay documentos para descargar -> next_action : "set_transaction_status"
            2. Sistema: No se ha descargadi el documento -> next_action: "rety"
        
## set_transaction_status
## end
 
        Ends the workflow. Closes any open resources like the web browser
        