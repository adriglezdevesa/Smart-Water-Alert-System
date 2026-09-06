import logica
import base_datos  

print("1. Inicializando la estructura de la base de datos...")
base_datos.inicializar_bd()  

print("2. Generando base de datos con 1.000 contadores y 24h de historial...")
logica.insertar_datos_prueba()

print("¡Base de datos generada con éxito! Ya puedes abrir la interfaz.")