import concurrent.futures
import sys 
import sqlite3
import os
from datetime import datetime, timedelta
from fpdf import FPDF

# --- LA SOLUCIÓN ESTÁ EN ESTAS DOS LÍNEAS ---
import matplotlib
matplotlib.use('Agg') # Obliga a Matplotlib a trabajar en segundo plano sin usar la interfaz gráfica
import matplotlib.pyplot as plt 
# -------------------------------------------

import random

# ---GPS PARA EL EJECUTABLE ---
def obtener_ruta_base():
    if getattr(sys, 'frozen', False):
        # Si el programa es un .exe, la carpeta base es donde esté guardado el .exe
        return os.path.dirname(sys.executable)
    else:
        # Si estamos programando en VS Code, la carpeta base es la carpeta padre de 'src'
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def conectar_bd():
    carpeta_datos = os.path.join(obtener_ruta_base(), 'datos')
    os.makedirs(carpeta_datos, exist_ok=True)  # La crea si no existe (p. ej. en un clon recién descargado)
    ruta_bd = os.path.join(carpeta_datos, 'agua_concello.db')
    return sqlite3.connect(ruta_bd)

def carpeta_informes():
    # Carpeta donde se guardan los PDF y las gráficas; se crea si no existe
    ruta = os.path.join(obtener_ruta_base(), 'informes')
    os.makedirs(ruta, exist_ok=True)
    return ruta

def insertar_datos_prueba():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    cursor.execute("DELETE FROM lecturas") 
    cursor.execute("DELETE FROM contadores") 
    
    # --- GENERADOR DE 1.000 CONTADORES ---
    vecinos = []
    
    # Bucle para generar 1000 casas (de C-0001 a C-1000)
    for i in range(1, 1001):
        id_cont = f'C-{i:04d}'  # Quedará como C-0001, C-0002...
        tipo = 'CASA'
        direccion = f'Vivenda {i}, Localidad de Prueba'
        titular = f'Veciño {i}'
        
        # Tiramos los dados (probabilidad del 0.0 al 1.0)
        prob = random.random()
        
        # 85% NORMALES (Verdes)
        if prob < 0.85:
            perfil = random.choice(['normal', 'ausente'])
        # 10% CONSUMO ALTO (Naranjas)
        elif prob < 0.95:
            perfil = random.choice(['piscina', 'riego_nocturno'])
        # 5% FUGAS Y AVERÍAS (Rojos)
        else:
            perfil = random.choice(['fuga_progresiva', 'rotura_subita', 'goteo_constante'])
            
        vecinos.append((id_cont, tipo, direccion, titular, perfil))
        
    # Añadimos un par de tanques municipales a mano para la prueba
    vecinos.append(('T-001', 'TANQUE', 'Depósito Central', 'Concello', 'tanque'))
    vecinos.append(('T-002', 'TANQUE', 'Depósito Ourense', 'Concello', 'tanque'))
    # ----------------------------------------

    # Aquí el código sigue exactamente igual que lo tenías:
    for v in vecinos:
        cursor.execute("INSERT INTO contadores VALUES (?, ?, ?, ?)", (v[0], v[1], v[2], v[3]))

    hora_actual = datetime.now()
    
    for i in range(24, -1, -1):
        hora_simulada = hora_actual - timedelta(hours=i)
        fecha_str = hora_simulada.strftime('%Y-%m-%d %H:%M:%S')
        hora = hora_simulada.hour
        
        for v in vecinos:
            id_cont = v[0]
            perfil = v[4]
            
            # --- COMPORTAMIENTOS REALISTAS ---
            if perfil == 'normal': 
                # Picos reales para una casa: entre 40 y 80 litros en horas punta
                if 7 <= hora <= 9 or 13 <= hora <= 15 or 20 <= hora <= 22: 
                    c = random.uniform(0.04, 0.08)
                else: 
                    c = random.uniform(0.001, 0.005)
                
            elif perfil == 'fuga_progresiva': # Juan: Se rompe un tubo y va a más
                if i > 12: c = random.uniform(0.02, 0.06)
                else: c = random.uniform(0.05, 0.1) + ((12-i)*0.08)
                
            elif perfil == 'piscina': # Pedro: Llena la piscina por la tarde
                if 12 <= hora <= 18: c = random.uniform(0.8, 1.1)
                else: c = random.uniform(0.01, 0.05)
                
            elif perfil == 'rotura_subita': # Lucía: Tubería revienta de golpe hace 4 horas
                if i > 4: c = random.uniform(0.01, 0.04)
                else: c = random.uniform(1.2, 1.5)
                
            elif perfil == 'riego_nocturno': # Carlos: Gasta a las 3 y 4 AM (Alerta Naranja)
                if 3 <= hora <= 4: c = random.uniform(0.6, 0.8)
                else: c = random.uniform(0.01, 0.04)
                
            elif perfil == 'ausente': # Ana: De vacaciones, consumo cero
                c = random.uniform(0.00, 0.001)
                
            elif perfil == 'goteo_constante': # Marta: Cisterna goteando las 24h
                c = random.uniform(0.12, 0.15)
                
            elif perfil == 'tanque':
                if 7 <= hora <= 23: c = random.uniform(1.5, 3.5)
                else: c = random.uniform(0.3, 0.8)
            
            cursor.execute("INSERT INTO lecturas (id_contador, fecha, consumo_m3) VALUES (?, ?, ?)", (id_cont, fecha_str, c))
            
    conexion.commit()
    conexion.close()

def crear_grafica_contador(id_contador, titular):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    # Le decimos al SQL que también nos traiga el TIPO (CASA o TANQUE)
    cursor.execute('''
        SELECT lecturas.fecha, lecturas.consumo_m3, contadores.tipo 
        FROM lecturas 
        JOIN contadores ON lecturas.id_contador = contadores.id_contador
        WHERE lecturas.id_contador = ? ORDER BY lecturas.fecha
    ''', (id_contador,))
    datos = cursor.fetchall()
    conexion.close()

    if not datos: return None

    fechas = [datetime.strptime(d[0], '%Y-%m-%d %H:%M:%S') for d in datos]
    consumos = [d[1] for d in datos]
    tipo_contador = datos[0][2] # CASA o TANQUE

    plt.figure(figsize=(8, 4)) 
    plt.plot(fechas, consumos, marker='o', color='red', linestyle='-')
    plt.title(f"Evolución del Consumo (Últimas 24h) - {titular}")
    plt.ylabel("Consumo (m3)")
    plt.xlabel("Hora")
    plt.xticks(rotation=45) 
    plt.grid(True)
    
    # LA MAGIA DE LA ESCALA: Le ponemos un "techo" mínimo para que las líneas bajas se vean aplastadas
    plt.ylim(bottom=0)
    max_consumo = max(consumos) if consumos else 0
    if tipo_contador == 'CASA' and max_consumo < 1.0:
        plt.ylim(top=1.0) # Si gasta menos de 1, la gráfica llega hasta 1 para verse proporcionada
    elif tipo_contador == 'TANQUE' and max_consumo < 5.0:
        plt.ylim(top=5.0)

    plt.tight_layout() 
    ruta_imagen = os.path.join(carpeta_informes(), f'grafica_{id_contador}.png')
    plt.savefig(ruta_imagen)
    plt.close() 
    return ruta_imagen

# ---PLANTILLA CON ENCABEZADO Y PIE DE PÁGINA ---
class PlantillaPDF(FPDF):
    def header(self):
        # Esto se imprime automáticamente arriba del todo en CADA página
        self.set_font("helvetica", "B", 14)
        self.set_text_color(50, 50, 50) # Gris oscuro
        self.cell(0, 10, "INFORME OFICIAL DE ALERTAS DE AGUA - CONCELLO", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        # Esto se imprime automáticamente abajo del todo (a 1.5 cm del borde)
        self.set_y(-15)
        self.set_font("helvetica", "I", 10)
        self.set_text_color(128, 128, 128) # Gris claro
        fecha_hoy = datetime.now().strftime('%d/%m/%Y %H:%M')
        # Ponemos la fecha y el número de página
        self.cell(0, 10, f"Generado el: {fecha_hoy}  |  Página {self.page_no()}", align="C")

# --- FUNCIÓN PARA EL PDF (Con auto-limpieza de fotos) ---
def generar_pdf_alertas(alertas):
    pdf = PlantillaPDF()
    imagenes_a_borrar = []
    
    def prioridad_riesgo(alerta):
        consumo_total = alerta[3]
        tipo = alerta[6]
        if tipo == 'CASA':
            if consumo_total > 5.0: return 1  # Subimos el límite rojo a 5 para evitar falsos positivos de piscinas
            elif consumo_total > 1.0: return 2
            else: return 3
        else: 
            if consumo_total > 50.0: return 1
            elif consumo_total > 20.0: return 2
            else: return 3
            
    alertas_ordenadas = sorted(alertas, key=lambda x: (prioridad_riesgo(x), -x[3]))

    # --- MAGIA MULTINÚCLEO: Generamos todas las gráficas de golpe en paralelo ---
    diccionario_graficas = {}
    
    # ProcessPoolExecutor lanza procesos paralelos usando todos los núcleos de tu CPU
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Preparamos las tareas
        futuros = {executor.submit(crear_grafica_contador, alerta[0], alerta[2]): alerta[0] for alerta in alertas_ordenadas}
        
        # A medida que los núcleos del procesador van terminando las fotos, las guardamos
        for futuro in concurrent.futures.as_completed(futuros):
            id_cont = futuros[futuro]
            diccionario_graficas[id_cont] = futuro.result()
    # -----------------------------------------------------------------------------

    # Ahora que ya están todas las fotos creadas en el disco duro, montamos el PDF rapidísimo
    for alerta in alertas_ordenadas:
        pdf.add_page()
        id_cont, direccion, titular, consumo_total, primera_fecha, ultima_fecha, tipo = alerta
        
        if tipo == 'CASA':
            if consumo_total > 5.0: color, titulo = (200, 0, 0), "[!] ALERTA GRAVE"
            elif consumo_total > 1.0: color, titulo = (255, 140, 0), "[!] AVISO: Consumo Alto"
            else: color, titulo = (0, 150, 0), "[OK] CONSUMO NORMAL"
        else: 
            if consumo_total > 50.0: color, titulo = (200, 0, 0), "[!] ALERTA GRAVE"
            elif consumo_total > 20.0: color, titulo = (255, 140, 0), "[!] AVISO: Consumo Alto"
            else: color, titulo = (0, 150, 0), "[OK] CONSUMO NORMAL"
        
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(*color)
        pdf.cell(0, 10, f"{titulo}: {titular}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        pdf.set_font("helvetica", "", 12)
        pdf.set_text_color(0, 0, 0) 
        pdf.cell(0, 8, f" - Dirección del contador: {direccion} (ID: {id_cont})", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f" - Consumo Total Detectado: {consumo_total:.2f} m3 ({(consumo_total*1000):.0f} litros)", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f" - Primer registro: {primera_fecha}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f" - Último registro: {ultima_fecha}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # Cogemos la ruta de la gráfica que ya generamos en el bloque anterior
        ruta_grafica = diccionario_graficas.get(id_cont)
        if ruta_grafica:
            pdf.image(ruta_grafica, x=20, w=170)
            imagenes_a_borrar.append(ruta_grafica)
            
    ruta_informe = os.path.join(carpeta_informes(), 'informe_alertas_graficas.pdf')
    pdf.output(ruta_informe)
    
    for ruta_img in imagenes_a_borrar:
        try:
            os.remove(ruta_img)
        except Exception:
            pass 
            
    return ruta_informe

def generar_informe_personalizado(lista_ids):
    if not lista_ids: return "❌ No has seleccionado a nadie.", None

    conexion = conectar_bd()
    cursor = conexion.cursor()
    interrogantes = ', '.join(['?'] * len(lista_ids))
    
    # Hemos añadido 'contadores.tipo' y 'ORDER BY' para que salgan ordenados de peor a mejor
    cursor.execute(f'''
        SELECT lecturas.id_contador, contadores.direccion, contadores.titular, 
               SUM(lecturas.consumo_m3) as consumo_total, 
               MIN(lecturas.fecha) as primera_fecha,
               MAX(lecturas.fecha) as ultima_fecha,
               contadores.tipo
        FROM lecturas 
        JOIN contadores ON lecturas.id_contador = contadores.id_contador
        WHERE lecturas.id_contador IN ({interrogantes})
        GROUP BY lecturas.id_contador
        ORDER BY consumo_total DESC 
    ''', lista_ids) 
    
    consumos_seleccionados = cursor.fetchall()
    conexion.close()
    
    if len(consumos_seleccionados) > 0:
        ruta_pdf = generar_pdf_alertas(consumos_seleccionados) 
        mensaje = f"[✓] PDF generado con éxito para {len(consumos_seleccionados)} contadores."
        return mensaje, ruta_pdf
    else:
        return "❌ No hay datos para los seleccionados.", None

# Devuelve el id_contador para que la interfaz pueda usarlo
def obtener_listado_clasificado(filtro_tipo="TODOS", filtro_riesgo="TODOS", busqueda=""):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT c.id_contador, c.tipo, c.direccion, c.titular, IFNULL(SUM(l.consumo_m3), 0)
        FROM contadores c
        LEFT JOIN lecturas l ON c.id_contador = l.id_contador
        GROUP BY c.id_contador
    ''')
    resultados = cursor.fetchall()
    conexion.close()

    lista_final = []
    for fila in resultados:
        id_cont, tipo, direccion, titular, consumo = fila
        if tipo == 'CASA':
            if consumo > 5.0: riesgo = "ROJO"
            elif consumo > 1.0: riesgo = "NARANJA"
            else: riesgo = "NORMAL"
        else:
            if consumo > 50.0: riesgo = "ROJO"
            elif consumo > 20.0: riesgo = "NARANJA"
            else: riesgo = "NORMAL"

        # Filtro de búsqueda por texto (ID o Nombre)
        if busqueda and busqueda.lower() not in id_cont.lower() and busqueda.lower() not in titular.lower():
            continue

        if filtro_tipo != "TODOS" and tipo != filtro_tipo: continue
        if filtro_riesgo != "TODOS" and riesgo != filtro_riesgo: continue
        
        lista_final.append({'id_contador': id_cont, 'tipo': tipo, 'titular': titular, 'direccion': direccion, 'consumo': consumo, 'riesgo': riesgo})

    orden_riesgo = {"ROJO": 1, "NARANJA": 2, "NORMAL": 3}
    lista_final.sort(key=lambda x: (orden_riesgo[x['riesgo']], -x['consumo']))
    return lista_final