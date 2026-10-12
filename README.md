# 💧 Smart Water Alert System (IoT Simulation)

Prototipo de aplicación de escritorio para la monitorización y la detección de consumos anómalos en la red de abastecimiento de aguas de un municipio. **Trabaja con datos simulados**: no se conecta a contadores reales.

El sistema analiza el consumo de 1.000 contadores simulados durante 24 horas, clasifica el riesgo de cada uno mediante umbrales de consumo y genera informes en PDF con la gráfica de cada caso.

## 🚀 Características Principales (Features)

*   **Generador de Datos Simulados (*Mock Data Profiling*):** Incluye un script (`generador_datos.py`) que simula 1.000 casas y 2 depósitos municipales durante 24 horas. Genera patrones de consumo verosímiles: *Goteo constante, Fuga progresiva, Riego nocturno, Rotura súbita o Uso de piscina*.
*   **Interfaz Gráfica Moderna:** UI desarrollada con `CustomTkinter` (soporte Modo Oscuro/Claro), con búsqueda en tiempo real y filtros por tipo de contador y nivel de riesgo.
*   **Generación de Informes en PDF:** Creación de informes (`fpdf2`) que incluyen la gráfica de consumo de cada contador seleccionado (`Matplotlib`), ordenados de mayor a menor riesgo.
*   **Procesamiento Paralelo (*Multiprocessing*):** Para evitar cuellos de botella al exportar cientos de gráficas, el sistema utiliza `concurrent.futures.ProcessPoolExecutor`, aprovechando todos los núcleos de la CPU para renderizar las imágenes en segundo plano.
*   **UI Asíncrona (*Multithreading*):** Delegación de la generación del informe a un hilo secundario (`threading.Thread`) para que la interfaz gráfica no se congele mientras se crea el PDF.

## 🚦 Cómo se clasifica el riesgo

La clasificación se basa en el consumo total acumulado de cada contador durante las 24 horas simuladas:

| Tipo de contador | 🟠 NARANJA (consumo alto) | 🔴 ROJO (alerta grave) |
| --- | --- | --- |
| Casa | más de 1 m³ | más de 5 m³ |
| Depósito | más de 20 m³ | más de 50 m³ |

El resto se considera consumo normal.

## 📸 Interfaz y Resultados (Screenshots)

### 1. Panel de Monitorización y Filtros
![Panel de Control1](img/panel1.png)
![Panel de Control2](img/panel2.png)

### 2. Informe PDF de Alerta Generado
![Informe PDF](img/pdf.png)

## 🛠️ Tecnologías y Arquitectura
*   **Backend & Lógica:** Python
*   **Base de Datos:** SQLite3 (Estructura relacional: Contadores, Lecturas, Alertas).
*   **GUI:** CustomTkinter
*   **Renderizado & Documentos:** Matplotlib (Motor `Agg` headless), fpdf2.

## ⚙️ Instalación y Uso (How to run)

1. Clona este repositorio en tu máquina local:
   ```bash
   git clone https://github.com/adriglezdevesa/Smart-Water-Alert-System.git
   cd Smart-Water-Alert-System
   ```

2. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```
   *(En Linux puede hacer falta instalar también Tkinter: `sudo apt install python3-tk`.)*

3. Genera la base de datos simulada. Crea las tablas e inserta 1.000 casas y 2 depósitos con patrones de consumo aleatorios (si ya existían datos, se reemplazan):
   ```bash
   python src/generador_datos.py
   ```

4. Ejecuta el Panel de Control:
   ```bash
   python src/interfaz.py
   ```

Los informes en PDF se guardan en la carpeta `informes/`.

## ⚠️ Limitaciones conocidas

*   **Datos simulados:** el proyecto es una demostración. No hay conexión con contadores ni sensores reales, y cada ejecución de `generador_datos.py` genera datos aleatorios nuevos.
*   **Clasificación por umbrales:** el riesgo se decide solo por el consumo total de 24 horas, así que no distingue el origen del gasto (por ejemplo, el llenado de una piscina y una tubería rota acaban igual de graves). Una mejora natural sería analizar el patrón de consumo: caudal mínimo nocturno y tendencia creciente.
*   **Alertas sin persistir:** la tabla `alertas` está creada en la base de datos, pero todavía no se utiliza para guardar un histórico de avisos.

---

**Autor:** Adrián González Devesa
