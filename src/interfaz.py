import customtkinter as ctk
import logica
import platform
import subprocess
import os
import threading
import webbrowser

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("700x600") 
app.title("Gestión de Agua - Concello")

# --- FUNCIÓN UNIVERSAL PARA ABRIR PDF ---
def abrir_pdf(ruta_pdf):
    ruta_absoluta = os.path.abspath(ruta_pdf)
    if platform.system() == 'Windows':
        os.startfile(ruta_absoluta)
    else:
        try:
            subprocess.Popen(['xdg-open', ruta_absoluta], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            webbrowser.open(f"file://{ruta_absoluta}")

# --- PESTAÑA 1: VER GRÁFICA INDIVIDUAL ---
def accion_ver_grafica_individual(id_cont, titular):
    # En lugar de generar un PDF, creamos solo la foto y la abrimos
    ruta_imagen = logica.crear_grafica_contador(id_cont, titular)
    if ruta_imagen:
        # Tu función abrir_pdf usa el gestor del sistema, así que abrirá el PNG con el visor de fotos de Windows
        abrir_pdf(ruta_imagen) 

def actualizar_lista_visual(valor=None): 
    # Borramos los resultados anteriores
    for widget in frame_lista_resultados.winfo_children():
        widget.destroy()
        
    # LEEMOS EL BUSCADOR DE LA PESTAÑA 1
    texto_busqueda = entrada_busqueda_1.get()
    
    # Le pasamos el texto a la lógica
    datos = logica.obtener_listado_clasificado(botones_tipo.get(), botones_riesgo.get(), texto_busqueda)
    
    if len(datos) == 0:
        ctk.CTkLabel(frame_lista_resultados, text="No hay resultados con estos filtros.").pack(pady=20)
        return

    if len(datos) > 150:
        aviso = ctk.CTkLabel(frame_lista_resultados, text=f"⚠️ Mostrando los 150 consumos más altos (de {len(datos)})", text_color="orange")
        aviso.pack(pady=5)
        datos = datos[:150]

    for d in datos:
        fila = ctk.CTkFrame(frame_lista_resultados, fg_color="transparent")
        fila.pack(fill="x", pady=2, padx=5)
        
        if d['riesgo'] == "ROJO": color_texto = "#FF3333"
        elif d['riesgo'] == "NARANJA": color_texto = "#FF9900"
        else: color_texto = "#33CC33"
        
        icono = "🏠" if d['tipo'] == "CASA" else "🛢️"
        texto = f"[{d['riesgo']}] {icono} {d['titular']} | {d['consumo']:.2f} m3 | {d['direccion']}"
        
        lbl = ctk.CTkLabel(fila, text=texto, text_color=color_texto, font=("Arial", 14, "bold"))
        lbl.pack(side="left")
        
        btn = ctk.CTkButton(fila, text="📈 Ver Gráfica", width=100, height=24, 
                            command=lambda id_c=d['id_contador'], tit=d['titular']: accion_ver_grafica_individual(id_c, tit))
        btn.pack(side="right")


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

# --- PESTAÑA 2: LÓGICA DE INFORME MULTIPLE ---
casillas_pdf = {}

def accion_analizar_multiples():
    ids_seleccionados = [id_cont for id_cont, datos in casillas_pdf.items() if datos['variable'].get() == "ON"]
            
    if len(ids_seleccionados) == 0:
        etiqueta_estado.configure(text="⚠️ Selecciona al menos a una persona.", text_color="red")
        return

    etiqueta_estado.configure(text="Generando PDF, por favor espera...", text_color="orange")
    boton_analizar.configure(state="disabled") # Bloqueamos el botón para que no le den dos veces
    app.update()
    
    # Creamos una función interna que se ejecutará en segundo plano
    def tarea_segundo_plano():
        mensaje, ruta_pdf = logica.generar_informe_personalizado(ids_seleccionados) 
        
        # Cuando termine, actualizamos la interfaz
        if ruta_pdf:
            etiqueta_estado.configure(text=mensaje, text_color="green")
            abrir_pdf(ruta_pdf)
        else:
            etiqueta_estado.configure(text=mensaje, text_color="red")
            
        boton_analizar.configure(state="normal") # Desbloqueamos el botón

    # Lanzamos el hilo
    hilo = threading.Thread(target=tarea_segundo_plano)
    hilo.start()

def actualizar_casillas_pdf(valor=None):
    # Borramos los widgets antiguos
    for widget in frame_scroll.winfo_children():
        widget.destroy()
    casillas_pdf.clear() # Limpiamos la memoria de las casillas
    
    # LEEMOS EL BUSCADOR DE LA PESTAÑA 2
    texto_busqueda = entrada_busqueda_2.get()
    datos = logica.obtener_listado_clasificado("TODOS", "TODOS", texto_busqueda)
    
    for d in datos:
        if d['riesgo'] == "NORMAL":
            continue

        var_casilla = ctk.StringVar(value="OFF") 
        texto_casilla = f"[{d['riesgo']}] {d['titular']} - {d['consumo']:.2f} m3"
        color_texto = "#FF3333" if d['riesgo'] == "ROJO" else "#FF9900"
        
        cb = ctk.CTkCheckBox(
            frame_scroll, text=texto_casilla, variable=var_casilla, 
            onvalue="ON", offvalue="OFF", text_color=color_texto, font=("Arial", 14, "bold")
        )
        cb.pack(pady=5, padx=10, anchor="w") 
        casillas_pdf[d['id_contador']] = {'widget': cb, 'variable': var_casilla, 'riesgo': d['riesgo']}
        
    seleccion_rapida("ROJOS_NARANJAS") # Volvemos a marcar las casillas automáticamente

def seleccion_rapida(filtro):
    for datos_casilla in casillas_pdf.values():
        datos_casilla['variable'].set("OFF")
        
    for datos_casilla in casillas_pdf.values():
        r = datos_casilla['riesgo']
        if filtro == "TODOS": datos_casilla['variable'].set("ON")
        elif filtro == "ROJOS" and r == "ROJO": datos_casilla['variable'].set("ON")
        elif filtro == "ROJOS_NARANJAS" and r in ["ROJO", "NARANJA"]: datos_casilla['variable'].set("ON")

# --- LÓGICA DEL PANEL PLEGABLE ---
def toggle_panel_config():
    if frame_configuracion.winfo_ismapped(): # Si está visible
        frame_configuracion.pack_forget() # Lo oculta
        boton_toggle.configure(text="⚙️ Mostrar Opciones Avanzadas de Selección")
    else:
        frame_configuracion.pack(before=boton_analizar, pady=5, fill="both", expand=True)
        boton_toggle.configure(text="⚙️ Ocultar Opciones Avanzadas")

# --- INICIALIZAMOS DATOS ---
#logica.insertar_datos_prueba()

# --- DISEÑO DE LA VENTANA ---
titulo = ctk.CTkLabel(app, text="Panel de Control de Aguas", font=("Arial", 22, "bold"))
titulo.pack(pady=10)

tabview = ctk.CTkTabview(app, width=650, height=500)
tabview.pack(padx=20, pady=5, fill="both", expand=True)

tab_lista = tabview.add("Listado Rápido")
tab_alertas = tabview.add("Generar Informe Oficial")

# --- CONTENIDO PESTAÑA 1 (La nueva lista) ---
# Añadimos el buscador arriba del todo
entrada_busqueda_1 = ctk.CTkEntry(tab_lista, placeholder_text="🔍 Buscar por ID o Vecino...", width=400)
entrada_busqueda_1.pack(pady=10)
# Esto hace que cada vez que sueltes una tecla, se actualice la lista sola
entrada_busqueda_1.bind("<KeyRelease>", actualizar_lista_visual)

botones_riesgo = ctk.CTkSegmentedButton(tab_lista, values=["TODOS", "ROJO", "NARANJA", "NORMAL"], command=actualizar_lista_visual)
botones_riesgo.set("TODOS")
botones_riesgo.pack(pady=5)
botones_tipo = ctk.CTkSegmentedButton(tab_lista, values=["TODOS", "CASA", "TANQUE"], command=actualizar_lista_visual)
botones_tipo.set("TODOS")
botones_tipo.pack(pady=5)

frame_lista_resultados = ctk.CTkScrollableFrame(tab_lista) 
frame_lista_resultados.pack(pady=10, fill="both", expand=True) 
actualizar_lista_visual()

# --- CONTENIDO PESTAÑA 2 (Panel Oculto) ---
lbl_instrucciones = ctk.CTkLabel(tab_alertas, text="Por defecto se generará un informe de las alertas Graves y Medias.", font=("Arial", 14))
lbl_instrucciones.pack(pady=10)

# Añadimos el buscador de la pestaña de PDFs
entrada_busqueda_2 = ctk.CTkEntry(tab_alertas, placeholder_text="🔍 Filtrar informe por ID o Vecino...", width=400)
entrada_busqueda_2.pack(pady=5)
entrada_busqueda_2.bind("<KeyRelease>", actualizar_casillas_pdf)

boton_toggle = ctk.CTkButton(tab_alertas, text="⚙️ Mostrar Opciones Avanzadas de Selección", fg_color="gray", command=toggle_panel_config)
boton_toggle.pack(pady=5)

frame_configuracion = ctk.CTkFrame(tab_alertas, fg_color="transparent")

frame_botones_rapidos = ctk.CTkFrame(frame_configuracion, fg_color="transparent")
frame_botones_rapidos.pack(pady=5)
ctk.CTkButton(frame_botones_rapidos, text="🔴 Solo Graves", width=110, command=lambda: seleccion_rapida("ROJOS")).pack(side="left", padx=5)
ctk.CTkButton(frame_botones_rapidos, text="🟠 Graves+Naranjas", width=140, command=lambda: seleccion_rapida("ROJOS_NARANJAS")).pack(side="left", padx=5)
ctk.CTkButton(frame_botones_rapidos, text="❌ Ninguno", width=90, fg_color="gray", command=lambda: seleccion_rapida("NINGUNO")).pack(side="left", padx=5)

frame_scroll = ctk.CTkScrollableFrame(frame_configuracion, width=500, height=200)
frame_scroll.pack(pady=5)

# OJO: Aquí llamamos a la nueva función en lugar de rellenar_casillas_pdf
actualizar_casillas_pdf() 

# EL BOTÓN PRINCIPAL (Solo una vez)
boton_analizar = ctk.CTkButton(
    tab_alertas, text="📄 Generar PDF Oficial", font=("Arial", 16, "bold"),
    width=300, height=50, command=accion_analizar_multiples
)
boton_analizar.pack(pady=20)

etiqueta_estado = ctk.CTkLabel(tab_alertas, text="Listo para trabajar.", font=("Arial", 14))
etiqueta_estado.pack(pady=5)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # El escudo para que PyInstaller no abra ventanas infinitas
    app.mainloop()