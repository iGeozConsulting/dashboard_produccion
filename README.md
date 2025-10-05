# 🛢️ Dashboard Interactivo de Producción de Pozo (Streamlit)

Este proyecto es una aplicación interactiva desarrollada con **Streamlit** y **Altair** que permite visualizar rápidamente los datos históricos de producción de un pozo petrolero a partir de un archivo CSV.

El objetivo es facilitar el análisis de tendencias, la identificación de periodos de paro y la evaluación del rendimiento del pozo (a través del **Corte de Agua**).

## 🚀 Instalación y Uso

### 1. Requisitos Previos

Asegúrate de tener **Python 3.x** instalado.

### 2. Entorno Virtual (Recomendado)

Crea y activa un entorno virtual para aislar las dependencias:

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En macOS/Linux
source venv/bin/activate
```

### 3. Instalación de Dependencias
Instala las librerías necesarias (Streamlit, Pandas y Altair):

```bash
pip install streamlit pandas altair
```

### 4. Ejecución de la Aplicación
Guarda el código de la aplicación en un archivo llamado, por ejemplo, app.py. Luego, ejecuta el siguiente comando en tu terminal:

```bash
streamlit run app.py
```

Esto abrirá la aplicación en tu navegador web por defecto.

## 💾 Estructura del Archivo de Datos (CSV)
La aplicación requiere que el archivo de entrada sea un CSV con un formato específico para que el procesamiento sea exitoso.

**Requisitos Clave:**
Delimitador: El archivo debe estar separado por punto y coma (";").

Columnas: Las siguientes cuatro columnas son obligatorias y deben aparecer en este orden para asegurar la correcta lectura inicial:

|Nombre de la Columna |Descripción|Formato Requerido|
|--------------|--------------|--------------|
|Fecha|La fecha del reporte diario.|DD/MM/AAAA|(Día/Mes/Año)|
|BFPD|Barriles de Fluido Por Día (Petróleo + Agua).|Numérico|
|Produccion_Petroleo|Barriles de Petróleo Por Día (BPD).|Numérico|
|BAPD|Barriles de Agua Por Día.|Numérico|

Nota: La aplicación es tolerante a variaciones en mayúsculas/minúsculas y espacios en los nombres de las columnas, pero se recomienda usar los nombres exactos o muy cercanos a los listados arriba para evitar errores. El formato de la Fecha es estricto: DD/MM/AAAA.

Ejemplo de las primeras líneas del CSV:

```
Fecha;BFPD;Produccion_Petroleo;BAPD
01/01/2024;1500;1200;300
02/01/2024;1490;1190;300
03/01/2024;0;0;0
04/01/2024;1510;1180;330
```

## ✨ Características del Dashboard
Una vez que se carga un archivo CSV válido, el dashboard genera tres visualizaciones interactivas:

### 1. Producción de Petróleo y Agua (Líneas Combinadas)
Muestra la tendencia histórica de la producción de Petróleo (BPD) y Agua (BPD) en una sola gráfica.

Permite identificar visualmente el aumento o disminución relativa de cada fluido.

### 2. Producción Mensual de Petróleo (Barras)
Utiliza un gráfico de barras para la producción de Petróleo.

Ideal para identificar Paros: Las barras de altura cero o muy bajas señalan claramente los días o periodos de inactividad o producción restringida.

### 3. Corte de Agua (Water Cut)
Muestra el porcentaje de agua en el fluido total $(BAPD/BFPD)×100$.

Indicador Clave de Rendimiento: El incremento de este porcentaje es un indicador fundamental de la madurez del pozo o de posibles problemas de acarreo de agua.