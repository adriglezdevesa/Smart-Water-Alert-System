import sqlite3
import os

# Esta función conecta con la base de datos y crea las tablas si no existen
def inicializar_bd():
    # Ruta donde se guardará el archivo de la base de datos
    # Sube un nivel desde 'src' y entra en 'datos'
    ruta_bd = os.path.join(os.path.dirname(__file__), '..', 'datos', 'agua_concello.db')
    
    # Nos conectamos (si el archivo no existe, SQLite lo crea automáticamente)
    conexion = sqlite3.connect(ruta_bd)
    cursor = conexion.cursor()

    # TABLA 1: CONTADORES (Información de las casas o tanques)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contadores (
            id_contador TEXT PRIMARY KEY,
            tipo TEXT, -- Puede ser 'CASA' o 'TANQUE'
            direccion TEXT,
            titular TEXT
        )
    ''')

    # TABLA 2: LECTURAS (Los datos que van entrando del agua consumida)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lecturas (
            id_lectura INTEGER PRIMARY KEY AUTOINCREMENT,
            id_contador TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            consumo_m3 REAL,
            FOREIGN KEY (id_contador) REFERENCES contadores (id_contador)
        )
    ''')

    # TABLA 3: ALERTAS (Para guardar el histórico de avisos de fugas o excesos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alertas (
            id_alerta INTEGER PRIMARY KEY AUTOINCREMENT,
            id_contador TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            motivo TEXT,
            revisado BOOLEAN DEFAULT 0, -- 0 es no revisado, 1 es ya revisado por el operario
            FOREIGN KEY (id_contador) REFERENCES contadores (id_contador)
        )
    ''')

    # Guardamos los cambios y cerramos
    conexion.commit()
    conexion.close()
    print(f"Base de datos inicializada correctamente en: {ruta_bd}")

# Esto hace que si ejecutamos este archivo directamente, se ejecute la función
if __name__ == "__main__":
    inicializar_bd()