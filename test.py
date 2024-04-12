from email_activities.mails import Mail

mail = Mail('envios@asesoriaheras.es', "Voz94497", 'asesoriaheras-es.mail.protection.outlook.com', 25, 'asesoriaheras-es.mail.protection.outlook.com', 993)

mail.send(["enrique.crespo.debenito@gmail.com"], "test", text="test", files=["Z:/Descargas/ACENTRA SERVICIOS LOGISTICOS SL_B95287355/2023/IMPUESTOS/4º TRIM. 2023/190_2023_ACENTRA SERVICIOS LOGISTICOS SL.pdf"] )

