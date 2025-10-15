import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import io

# --- Configuración de la página ---
st.set_page_config(
    page_title="Dashboard de Producción y Análisis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Funciones de Ajuste ---
def exp_func(x, a, b):
    return a * np.exp(b * x)

def poly2_func(x, a, b, c):
    return a * x**2 + b * x + c

# --- 1. FUNCIÓN CENTRAL DE CÁLCULO ---
def realizar_calculos_chan(df):
    """
    Realiza todos los cálculos y ajustes de curvas una sola vez.
    Devuelve un diccionario con todos los resultados para ser reutilizados.
    """
    try:
        df_chan = df.copy().sort_values(by='FECHA')
        fecha_inicio = df_chan['FECHA'].min()
        dias = (df_chan['FECHA'] - fecha_inicio).dt.days.to_numpy()
        petroleo = df_chan['PRODUCCION_PETROLEO'].to_numpy()
        agua = df_chan['BAPD'].to_numpy()

        wor = np.divide(agua, petroleo, out=np.full_like(agua, np.nan, dtype=float), where=petroleo != 0)
        derivada = np.gradient(wor, dias)
        
        valid_idx = np.isfinite(wor) & np.isfinite(derivada) & (wor > 0) & (derivada > 0)
        if np.sum(valid_idx) < 3:
            return None # No hay suficientes datos

        # Realizar ajustes de curvas
        popt_exp, popt_wor, popt_derivada = None, None, None
        try: popt_exp, _ = curve_fit(exp_func, dias, petroleo, p0=[petroleo[0], -1e-3], maxfev=10000)
        except RuntimeError: pass
        try: popt_wor, _ = curve_fit(poly2_func, dias[valid_idx], wor[valid_idx])
        except RuntimeError: pass
        try: popt_derivada, _ = curve_fit(poly2_func, dias[valid_idx], derivada[valid_idx])
        except RuntimeError: pass
        
        resultados = {
            "df_chan": df_chan, "dias": dias, "petroleo": petroleo, "agua": agua,
            "wor": wor, "derivada": derivada, "valid_idx": valid_idx,
            "popt_exp": popt_exp, "popt_wor": popt_wor, "popt_derivada": popt_derivada
        }
        return resultados
    except Exception:
        return None

# --- 2. FUNCIÓN PARA GENERAR IMAGEN ESTÁTICA (PNG) ---
def generar_imagen_matplotlib(datos, file_name):
    """
    Genera la imagen de diagnóstico COMPLETA con Matplotlib para ser descargada.
    """
    dias, petroleo, wor, derivada = datos['dias'], datos['petroleo'], datos['wor'], datos['derivada']
    valid_idx = datos['valid_idx']
    popt_exp, popt_wor, popt_derivada = datos['popt_exp'], datos['popt_wor'], datos['popt_derivada']

    fig, ax = plt.subplots(1, 2, figsize=(18, 8), dpi=150)
    fig.suptitle(f'Diagnóstico de Chan - Pozo: {file_name}', fontsize=18, fontweight='bold')

    # Subplot 1
    ax[0].scatter(dias, petroleo, label='Producción Real', color='teal', alpha=0.7, s=30)
    if popt_exp is not None:
        ax[0].plot(dias, exp_func(dias, *popt_exp), label='Ajuste Exponencial', color='red', linestyle='--')
    ax[0].set_title('Declinación de Producción de Petróleo', fontsize=14)
    ax[0].set_xlabel('Días Transcurridos'); ax[0].set_ylabel('Producción (BPD)'); ax[0].legend(); ax[0].grid(True, alpha=0.4)

    # Subplot 2
    dias_validos = dias[valid_idx]
    ax[1].scatter(dias_validos, wor[valid_idx], label='WOR Real', color='blue', alpha=0.7, s=30)
    if popt_wor is not None:
        ax[1].plot(dias_validos, poly2_func(dias_validos, *popt_wor), label='Ajuste WOR (Poly-2)', color='cornflowerblue')
    ax[1].scatter(dias_validos, derivada[valid_idx], label='Derivada WOR Real', color='green', alpha=0.7, s=30)
    if popt_derivada is not None:
        ax[1].plot(dias_validos, poly2_func(dias_validos, *popt_derivada), label='Ajuste Derivada (Poly-2)', color='lightgreen')
    ax[1].set_yscale('log')
    ax[1].set_title('Evolución de WOR y Derivada', fontsize=14)
    ax[1].set_xlabel('Días Transcurridos'); ax[1].set_ylabel('Valor (escala log)'); ax[1].legend(); ax[1].grid(True, which='both', alpha=0.4)
    
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', bbox_inches='tight')
    plt.close(fig)
    return img_buffer

# --- 3. FUNCIÓN PARA GRÁFICOS INTERACTIVOS (PLOTLY) ---
def mostrar_graficos_plotly(datos):
    """Muestra los gráficos interactivos de Plotly en el dashboard."""
    dias, petroleo, wor, derivada = datos['dias'], datos['petroleo'], datos['wor'], datos['derivada']
    valid_idx = datos['valid_idx']
    popt_exp, popt_wor, popt_derivada = datos['popt_exp'], datos['popt_wor'], datos['popt_derivada']
    dias_validos = dias[valid_idx]

    # Gráfico 1: Declinación
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=dias, y=petroleo, mode='markers', name='Producción Real', marker_color='teal'))
    # CORRECCIÓN AQUÍ
    if popt_exp is not None:
        fig1.add_trace(go.Scatter(x=dias, y=exp_func(dias, *popt_exp), mode='lines', name='Ajuste Exponencial', line_color='red'))
    fig1.update_layout(title='1. Declinación de Producción de Petróleo', template='plotly_white')
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2: Evolución WOR y Derivada
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=dias_validos, y=wor[valid_idx], mode='markers', name='WOR Real', marker_color='blue'))
    # CORRECCIÓN AQUÍ
    if popt_wor is not None:
        fig2.add_trace(go.Scatter(x=dias_validos, y=poly2_func(dias_validos, *popt_wor), mode='lines', name='Ajuste WOR', line_color='cornflowerblue'))
    fig2.add_trace(go.Scatter(x=dias_validos, y=derivada[valid_idx], mode='markers', name='Derivada WOR Real', marker_color='green'))
    # CORRECCIÓN AQUÍ
    if popt_derivada is not None:
        fig2.add_trace(go.Scatter(x=dias_validos, y=poly2_func(dias_validos, *popt_derivada), mode='lines', name='Ajuste Derivada', line_color='lightgreen'))
    fig2.update_layout(title="2. Evolución de WOR y Derivada (vs. Tiempo)", yaxis_type='log', template='plotly_white')
    st.plotly_chart(fig2, use_container_width=True)
    
    # Gráfico 3: Diagnóstico Chan
    fig3 = go.Figure(data=go.Scatter(x=wor[valid_idx], y=derivada[valid_idx], mode='markers', marker_color='purple'))
    fig3.update_layout(title="3. Gráfico de Diagnóstico (WOR vs. Derivada')", xaxis_type='log', yaxis_type='log', template='plotly_white')
    st.plotly_chart(fig3, use_container_width=True)

# --- INTERFAZ PRINCIPAL DEL DASHBOARD ---
st.title("🛢️ Dashboard de Producción y Análisis de Yacimientos")

COL_FECHA, COL_BFPD, COL_PROD, COL_BAPD = 'FECHA', 'BFPD', 'PRODUCCION_PETROLEO', 'BAPD'
COLUMNAS_REQUERIDAS = [COL_FECHA, COL_BFPD, COL_PROD, COL_BAPD]

uploaded_file = st.file_uploader("Sube el archivo CSV (delimitado por ';') con las columnas: Fecha, BFPD, Produccion_Petroleo, BAPD", type=["csv"])

if uploaded_file is not None:
    st.session_state.file_name = uploaded_file.name.replace('.csv', '', 1).replace('.CSV', '', 1)
    
    try:
        df = pd.read_csv(uploaded_file, sep=';')
        df.columns = [col.strip().replace(' ', '_').upper() for col in df.columns]
        
        if not all(col in df.columns for col in COLUMNAS_REQUERIDAS):
            missing = [col for col in COLUMNAS_REQUERIDAS if col not in df.columns]
            st.error(f"¡Error! Faltan columnas requeridas en tu archivo: {missing}.")
        else:
            st.success(f"Archivo '{st.session_state.file_name}.csv' cargado y procesado.")
            
            df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], errors='coerce', dayfirst=True)
            for col in [COL_BFPD, COL_PROD, COL_BAPD]: df[col] = pd.to_numeric(df[col], errors='coerce')
            df.dropna(subset=COLUMNAS_REQUERIDAS, inplace=True)

            if df.empty:
                st.warning("El archivo no contiene filas con datos válidos después de la limpieza.")
            else:
                tab1, tab2 = st.tabs(["📊 Dashboard de Producción", "📈 Análisis de Curvas de Chan"])

                with tab1:
                    st.header(f"⛽ Reporte de Producción: **{st.session_state.file_name}**")
                    df['CORTE_DE_AGUA'] = np.divide(df[COL_BAPD], df[COL_BFPD], out=np.zeros_like(df[COL_BFPD], dtype=float), where=df[COL_BFPD]!=0) * 100
                    st.subheader("1. Producción de Petróleo y Agua")
                    df_melt = df.melt(id_vars=[COL_FECHA], value_vars=[COL_PROD, COL_BAPD], var_name='Variable', value_name='Flujo')
                    chart1 = alt.Chart(df_melt).mark_line(point=True).encode(x=f'{COL_FECHA}:T', y='Flujo:Q', color='Variable:N').interactive()
                    st.altair_chart(chart1, use_container_width=True)
                    st.subheader("2. Evolución del Corte de Agua (Water Cut)")
                    chart3 = alt.Chart(df).mark_line(point=True, color='#d62728').encode(x=f'{COL_FECHA}:T', y='CORTE_DE_AGUA:Q').interactive()
                    st.altair_chart(chart3, use_container_width=True)

                with tab2:
                    st.header("📈 Análisis de Diagnóstico con Curvas de Chan")
                    
                    datos_calculados = realizar_calculos_chan(df.copy())
                    
                    if datos_calculados:
                        st.info("La siguiente imagen estática está lista para ser descargada para tus reportes.")
                        img_buffer = generar_imagen_matplotlib(datos_calculados, st.session_state.file_name)
                        st.download_button(
                            label="📥 Descargar Gráfico de Diagnóstico (PNG)",
                            data=img_buffer.getvalue(),
                            file_name=f"diagnostico_chan_{st.session_state.file_name}.png",
                            mime="image/png"
                        )
                        st.markdown("---")
                        st.subheader("Análisis Interactivo")
                        mostrar_graficos_plotly(datos_calculados)
                    else:
                        st.warning("No se pudieron generar los análisis. No hay suficientes datos válidos (>0) en el archivo.")

    except Exception as e:
        st.error(f"Ocurrió un error general al procesar el archivo: {e}")
else:
    st.info("👋 ¡Bienvenido! Carga un archivo CSV de producción para comenzar el análisis.")