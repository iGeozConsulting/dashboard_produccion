import streamlit as st
import pandas as pd
import altair as alt

# --- Configuración de la página ---
st.set_page_config(
    page_title="Dashboard de Producción Petrolera",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título inicial mientras se espera la carga
st.title("🛢️ Dashboard Interactivo de Producción de Pozo")

# --- Constantes para nombres de columnas (usamos MAYÚSCULAS para consistencia) ---
COL_FECHA = 'FECHA'
COL_BFPD = 'BFPD'
COL_PROD = 'PRODUCCION_PETROLEO'
COL_BAPD = 'BAPD'
COL_CORTE_AGUA = 'CORTE_DE_AGUA'

# --- Carga de archivos ---
uploaded_file = st.file_uploader(
    "Sube el archivo CSV del reporte de producción (¡Debe estar separado por punto y coma ';'!):",
    type=["csv"]
)

if uploaded_file is not None:
    
    # --- Lógica para Título Dinámico ---
    # Obtener el nombre del archivo y limpiarlo para el título
    file_name = uploaded_file.name
    title_name = file_name.replace('.csv', '').replace('.CSV', '') 

    # Reemplazar el título inicial con el título dinámico del pozo
    st.header(f"⛽ Reporte de Producción del Pozo: **{title_name}**")
    st.markdown("---")
    
    # --- 1. Carga y pre-procesamiento de datos ---
    try:
        # CORRECCIÓN CLAVE: Usar sep=';' para manejar el delimitador de punto y coma
        df = pd.read_csv(uploaded_file, sep=';')
        
        # Limpieza robusta de nombres de columnas: strip, replace spaces, y to UPPER
        df.columns = [col.strip().replace(' ', '_').upper() for col in df.columns]

        # Validación de columnas
        required_cols = [COL_FECHA, COL_BFPD, COL_PROD, COL_BAPD]
        if not all(col in df.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df.columns]
            st.error(f"¡Error! Faltan columnas requeridas o los nombres no coinciden. Faltantes: {missing_cols}")
        
        st.success(f"Datos cargados y limpiados correctamente. Filas: {len(df)}")
        
        # Conversión de tipos
        df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], errors='coerce', dayfirst=True)
        df.dropna(subset=[COL_FECHA], inplace=True)
        
        for col in [COL_BFPD, COL_PROD, COL_BAPD]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df.dropna(subset=[COL_BFPD, COL_PROD, COL_BAPD], inplace=True)

        # --- 2. Cálculos para gráficas ---
        
        # Cálculo del Corte de Agua (Water Cut)
        df[COL_CORTE_AGUA] = (df[COL_BAPD] / df[COL_BFPD]) * 100
        df.loc[df[COL_BFPD] == 0, COL_CORTE_AGUA] = 0 

        # ----------------------------------------------------------------------
        # GRÁFICA 1: Producción de Petróleo y Agua (Línea Combinada)
        # ----------------------------------------------------------------------

        # Preparar datos para Altair (formato largo)
        df_melt = df.melt(
            id_vars=[COL_FECHA],
            value_vars=[COL_PROD, COL_BAPD],
            var_name='Variable',
            value_name='Flujo'
        )

        chart1 = alt.Chart(df_melt).mark_line(point=True).encode(
            x=alt.X(COL_FECHA, title='Fecha (Mensual)', axis=alt.Axis(format="%Y-%m")),
            y=alt.Y('Flujo', title='Flujo (Barriles Por Día - BPD)'),
            color=alt.Color('Variable', 
                            title='Flujo de', 
                            scale=alt.Scale(domain=[COL_PROD, COL_BAPD], 
                                            range=['#008080', '#1f77b4'])),
            tooltip=[
                alt.Tooltip(COL_FECHA, title='Fecha', format="%Y-%m-%d"),
                alt.Tooltip('Variable', title='Variable'),
                alt.Tooltip('Flujo', title='BPD', format=',.2f')
            ]
        ).properties(
            title="1. Producción de Petróleo y Agua (Líneas Combinadas)"
        ).interactive() # Permite zoom y paneo
        
        st.subheader("1. Producción de Petróleo y Agua (Líneas Combinadas)")
        st.altair_chart(chart1, use_container_width=True)
        st.markdown("*Recuerda: Puedes descargar la gráfica como PNG o SVG haciendo clic en los 3 puntos (⋮) al pasar el cursor sobre ella.*")
        st.markdown("---")

        # Configuración base para el tooltip de las siguientes gráficas
        base_chart = alt.Chart(df).encode(
            x=alt.X(COL_FECHA, title='Fecha (Mensual)', axis=alt.Axis(format="%Y-%m")),
            tooltip=[
                alt.Tooltip(COL_FECHA, title='Fecha', format="%Y-%m-%d"),
                alt.Tooltip(COL_PROD, title='Petróleo (BPD)', format=',.2f'),
                alt.Tooltip(COL_BAPD, title='Agua (BPD)', format=',.2f'),
                alt.Tooltip(COL_CORTE_AGUA, title='Corte de Agua (%)', format=',.2f')
            ]
        ).interactive()

        # ----------------------------------------------------------------------
        # GRÁFICA 2: Producción de Petróleo (Barras para visualizar Paros)
        # ----------------------------------------------------------------------
        st.subheader("2. Producción Mensual de Petróleo (Barras)")
        st.info(
            "***Gráfico recomendado para Paros:*** Las barras de altura cero o muy bajas indican claramente periodos de paro o producción restringida."
        )
        
        chart2 = base_chart.mark_bar(color='#008080').encode(
            y=alt.Y(COL_PROD, title='Petróleo (Barriles Por Día - BPD)'),
        ).properties(
            title="Magnitud de la Producción Mensual de Petróleo (BPD)"
        )

        st.altair_chart(chart2, use_container_width=True)
        st.markdown("---")

        # ----------------------------------------------------------------------
        # GRÁFICA 3: Corte de Agua (Indicador de Rendimiento)
        # ----------------------------------------------------------------------
        
        st.subheader("3. Corte de Agua (Water Cut)")
        st.info(
            "***Gráfico de Rendimiento:*** Un incremento rápido en el Corte de Agua es un indicador clave de problemas o madurez del pozo."
        )
        
        chart3 = base_chart.mark_line(point=True, color='#d62728').encode(
            y=alt.Y(COL_CORTE_AGUA, title='Corte de Agua (%)', scale=alt.Scale(domain=[0, 100])),
        ).properties(
            title="Porcentaje de Agua en el Fluido Total (Corte de Agua)"
        )

        st.altair_chart(chart3, use_container_width=True)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
        st.warning("Verifica que el archivo esté separado por **punto y coma (;) ** y contenga las columnas: **Fecha, BFPD, Produccion_Petroleo, BAPD**.")

else:
    st.info("Esperando la carga de un archivo CSV...")