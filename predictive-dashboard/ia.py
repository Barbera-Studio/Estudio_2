import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import json

# 🛠️ Configuración de la app
st.set_page_config(page_title="Simulador Económico y Fiscal", layout="wide")

# ===========================
# 🧠 TÍTULO Y DESCRIPCIÓN LARGA
# ===========================
st.title("📈 Simulador de Impacto Económico y Fiscal")

st.markdown(
    """
Este simulador interactivo permite explorar, de forma intuitiva y visual, **cómo diferentes decisiones de política económica y fiscal afectan la trayectoria de una economía simulada** a lo largo del tiempo.

La herramienta está dividida en **dos grandes bloques**:

1. **Simulador de Impacto Económico**  
   - **Escenario Base:** Representa una economía que crece únicamente según una tasa de crecimiento natural anual.  
   - **Gasto sin retorno:** Muestra qué ocurre cuando se realizan gastos que no generan aumentos duraderos en el nivel de actividad, más allá del crecimiento natural.  
   - **Inversión productiva:** Simula el efecto de una inversión con retorno, modulada por un multiplicador de inversión, con impacto gradual en los primeros años y efectos más permanentes después.  
   - **Escenarios adicionales:**  
     - *Shock negativo en 2028:* Introduce un impacto adverso puntual en el año 2028.  
     - *Reforma estructural en 2030:* Aplica una mejora persistente a partir de 2030, que refuerza los efectos de la inversión.  
   - **Incertidumbre:** Se muestran bandas alrededor del escenario de inversión que representan un margen de incertidumbre, útil para visualizar riesgos y variación potencial de resultados.

2. **Simulador Fiscal**  
   - **Gasto público:** Se define como un porcentaje del índice económico simulado.  
   - **Ingresos fiscales base:** También definidos como porcentaje del índice, representando la recaudación sin reformas.  
   - **Reforma tributaria / consolidación fiscal:**  
     - *Reforma tributaria en 2028:* Aumenta los ingresos fiscales a partir de ese año.  
     - *Consolidación fiscal en 2029:* Introduce un ajuste más moderado, reflejando un proceso gradual de mejora de las cuentas públicas.  
   - A partir de estos parámetros, se calculan:  
     - **Déficit anual (% del índice económico):** Diferencia entre gasto e ingresos cada año.  
     - **Deuda acumulada (% del índice):** Suma a lo largo del tiempo de los déficits anuales, mostrando el efecto de la política fiscal a medio plazo.

---

### ¿Qué representa el “índice económico”?

El modelo no trabaja con una magnitud monetaria concreta (como millones de euros), sino con un **índice económico simulado** que parte de un valor base igual a `100`.  
Esto permite centrar la atención en las **trayectorias relativas** (cómo cambian los niveles con distintas decisiones) más que en cifras absolutas.  

---

### Cómo usar el simulador

- Ajusta los **sliders** para cambiar:  
  - El multiplicador de inversión.  
  - La tasa de crecimiento natural.  
  - El margen de incertidumbre.  
  - El tipo de escenario adicional (shock o reforma).  
- En la segunda parte, configura:  
  - El gasto público como porcentaje del índice.  
  - Los ingresos fiscales base.  
  - El impacto de una posible reforma tributaria o consolidación fiscal.  
- Observa cómo se actualizan automáticamente:  
  - El gráfico de impacto económico.  
  - El gráfico fiscal con déficit y deuda acumulada.  
- Al final, puedes **descargar los datos** en CSV o Excel, así como guardar un **preset** con la configuración actual para reutilizarla.

Esta herramienta está pensada para **ilustrar conceptos macroeconómicos y fiscales** de manera accesible, facilitando conversaciones y análisis sobre políticas de inversión, gasto público, reformas y sostenibilidad fiscal a lo largo del tiempo.
"""
)

st.markdown("---")

# ===========================
# 🎛️ PARÁMETROS ECONÓMICOS
# ===========================

st.subheader("⚙️ Parámetros del escenario económico")

col_econ_1, col_econ_2 = st.columns([1, 1])

with col_econ_1:
    multiplicador = st.slider("Multiplicador de inversión", 1.0, 3.0, 2.0, 0.1)
    tasa_crecimiento = st.slider(
        "Tasa de crecimiento natural (%)", 0.0, 3.0, 1.5, 0.1
    ) / 100

with col_econ_2:
    incertidumbre_pct = st.slider(
        "Margen de incertidumbre sobre inversión (%)", 0.0, 50.0, 25.0, 1.0
    ) / 100
    evento = st.selectbox(
        "Escenario adicional",
        ["Ninguno", "Shock negativo en 2028", "Reforma estructural en 2030"],
    )

# 📊 Datos base para impacto económico
ultimo_valor_base = 100
años_futuros = list(range(2025, 2036))
df = pd.DataFrame({"Año": años_futuros})

# Escenario base
df["Escenario_Base"] = [
    ultimo_valor_base * ((1 + tasa_crecimiento) ** (año - 2025))
    for año in años_futuros
]

# Escenario sin retorno
valor_gasto = ultimo_valor_base
valores_gasto = []
for año in años_futuros:
    if 2025 <= año <= 2029:
        valor_gasto += 0
    else:
        valor_gasto *= (1 + tasa_crecimiento)
    valores_gasto.append(valor_gasto)
df["Gasto_sin_retorno"] = valores_gasto

# Escenario con inversión
impacto_total = 2.0 * multiplicador
impacto_anual = impacto_total / 5
valores_inversion = []
valor = ultimo_valor_base

for año in años_futuros:
    if 2025 <= año <= 2029:
        # Impacto gradual de la inversión en los primeros años
        valor *= (1 + impacto_anual / 100)
    elif año >= 2030:
        # Consolidación de un mayor nivel derivado de la inversión
        valor *= (1 + impacto_total / 100)
    else:
        # Años intermedios: solo crecimiento natural
        valor *= (1 + tasa_crecimiento)

    # Escenarios adicionales
    if evento == "Shock negativo en 2028" and año == 2028:
        valor *= 0.95  # caída del 5% en ese año
    elif evento == "Reforma estructural en 2030" and año >= 2030:
        valor *= 1.03  # mejora adicional y sostenida del 3%

    valores_inversion.append(valor)

df["Inversión"] = valores_inversion

# Bandas de incertidumbre sobre el escenario de inversión
sup = df["Inversión"] * (1 + incertidumbre_pct)
inf = df["Inversión"] * (1 - incertidumbre_pct)

# ===========================
# 📈 GRÁFICO DE IMPACTO ECONÓMICO
# ===========================

st.subheader("📈 Simulación de impacto económico")

fig_econ = go.Figure()

fig_econ.add_trace(
    go.Scatter(
        x=df["Año"],
        y=df["Escenario_Base"],
        mode="lines+markers",
        name="Escenario Base",
        line=dict(dash="dash", color="gray"),
        hovertemplate="Año: %{x}<br>Base: %{y:.2f}",
    )
)

fig_econ.add_trace(
    go.Scatter(
        x=df["Año"],
        y=df["Gasto_sin_retorno"],
        mode="lines+markers",
        name="Gasto sin retorno",
        line=dict(dash="dot", color="red"),
        hovertemplate="Año: %{x}<br>Sin retorno: %{y:.2f}",
    )
)

fig_econ.add_trace(
    go.Scatter(
        x=df["Año"],
        y=df["Inversión"],
        mode="lines+markers",
        name=f"Inversión {multiplicador:.1f}x",
        line=dict(color="blue"),
        hovertemplate="Año: %{x}<br>Inversión: %{y:.2f}",
    )
)

# Relleno de incertidumbre
x_fill = df["Año"].tolist() + df["Año"][::-1].tolist()
y_fill = sup.tolist() + inf[::-1].tolist()

fig_econ.add_trace(
    go.Scatter(
        x=x_fill,
        y=y_fill,
        fill="toself",
        fillcolor="rgba(255,165,0,0.2)",
        line=dict(color="rgba(255,165,0,0)"),
        hoverinfo="skip",
        showlegend=True,
        name=f"±{int(incertidumbre_pct * 100)}% Incertidumbre",
    )
)

# Anotaciones finales
fig_econ.add_annotation(
    x=df["Año"].iloc[-1],
    y=df["Escenario_Base"].iloc[-1],
    text="Base",
    showarrow=False,
    font=dict(color="gray", size=12),
    xanchor="left",
)
fig_econ.add_annotation(
    x=df["Año"].iloc[-1],
    y=df["Gasto_sin_retorno"].iloc[-1],
    text="Sin retorno",
    showarrow=False,
    font=dict(color="red", size=12),
    xanchor="left",
)
fig_econ.add_annotation(
    x=df["Año"].iloc[-1],
    y=df["Inversión"].iloc[-1],
    text=f"{multiplicador:.1f}x",
    showarrow=False,
    font=dict(color="blue", size=12),
    xanchor="left",
)

fig_econ.update_layout(
    title="Simulación de Impacto Económico",
    xaxis_title="Año",
    yaxis_title="Índice Económico Simulado",
    hovermode="x unified",
    template="plotly_white",
    legend=dict(orientation="h", y=-0.2),
)

st.plotly_chart(fig_econ, use_container_width=True)

st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)

# ===========================
# 📊 SIMULADOR FISCAL
# ===========================

st.subheader("📊 Simulador fiscal sobre el índice económico")

col_fiscal_1, col_fiscal_2 = st.columns([1, 1])

with col_fiscal_1:
    gasto_pct = st.slider(
        "Gasto público (% del índice económico)",
        3.0,
        10.0,
        5.0,
        0.1,
    )
    ingresos_base = st.slider(
        "Ingresos fiscales base (% del índice económico)",
        3.0,
        10.0,
        4.0,
        0.1,
    )

with col_fiscal_2:
    incremento_reforma = st.slider(
        "Incremento por reforma tributaria (%)",
        0.0,
        3.0,
        1.0,
        0.1,
    )
    escenario_fiscal = st.selectbox(
        "Escenario fiscal",
        ["Ninguno", "Reforma tributaria en 2028", "Consolidación fiscal en 2029"],
    )

# 📉 Cálculo fiscal
ingresos_pct = ingresos_base
for i, año in enumerate(años_futuros):
    if escenario_fiscal == "Reforma tributaria en 2028" and año >= 2028:
        ingresos_pct = ingresos_base + incremento_reforma
    elif escenario_fiscal == "Consolidación fiscal en 2029" and año >= 2029:
        ingresos_pct = ingresos_base + incremento_reforma / 2
    else:
        ingresos_pct = ingresos_base

    df.loc[i, "Déficit"] = df["Inversión"].iloc[i] * (gasto_pct - ingresos_pct) / 100

df["Déficit_pct"] = df["Déficit"] / df["Inversión"] * 100
df["Deuda_Acumulada"] = df["Déficit"].cumsum()
df["Deuda_pct"] = df["Deuda_Acumulada"] / df["Inversión"] * 100

# 📉 Gráfico fiscal interactivo con Plotly
fig_fiscal = go.Figure()

fig_fiscal.add_trace(
    go.Scatter(
        x=df["Año"],
        y=df["Déficit_pct"],
        mode="lines+markers",
        name="Déficit (% del índice)",
        line=dict(color="crimson"),
        hovertemplate="Año: %{x}<br>Déficit: %{y:.2f}%",
    )
)
fig_fiscal.add_trace(
    go.Scatter(
        x=df["Año"],
        y=df["Deuda_pct"],
        mode="lines+markers",
        name="Deuda acumulada (% del índice)",
        line=dict(color="black"),
        hovertemplate="Año: %{x}<br>Deuda: %{y:.2f}%",
    )
)

# Etiquetas finales
fig_fiscal.add_annotation(
    x=df["Año"].iloc[-1],
    y=df["Déficit_pct"].iloc[-1],
    text="Déficit estructural",
    showarrow=False,
    font=dict(color="crimson", size=12),
    xanchor="left",
)
fig_fiscal.add_annotation(
    x=df["Año"].iloc[-1],
    y=df["Deuda_pct"].iloc[-1],
    text="Deuda por inversión productiva",
    showarrow=False,
    font=dict(color="black", size=12),
    xanchor="left",
)

fig_fiscal.update_layout(
    title="Simulación Fiscal (% del índice económico)",
    xaxis_title="Año",
    yaxis_title="% del índice",
    hovermode="x unified",
    template="plotly_white",
    legend=dict(orientation="h", y=-0.2),
)

st.plotly_chart(fig_fiscal, use_container_width=True)

st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

# ===========================
# 📤 EXPORTACIÓN DE RESULTADOS
# ===========================

st.subheader("📥 Exportar resultados y configuración")

col_export_1, col_export_2, col_export_3 = st.columns([1, 1, 1])

with col_export_1:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Descargar CSV",
        data=csv,
        file_name="simulacion_economica.csv",
        mime="text/csv",
    )

with col_export_2:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Simulación")
    st.download_button(
        "📥 Descargar Excel",
        data=output.getvalue(),
        file_name="simulacion_economica.xlsx",
        mime="application/"
        "vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with col_export_3:
    preset = {
        "multiplicador": multiplicador,
        "tasa_crecimiento": tasa_crecimiento,
        "incertidumbre_pct": incertidumbre_pct,
        "evento": evento,
        "gasto_pct": gasto_pct,
        "ingresos_base": ingresos_base,
        "incremento_reforma": incremento_reforma,
        "escenario_fiscal": escenario_fiscal,
    }
    preset_json = json.dumps(preset, ensure_ascii=False, indent=2)
    st.download_button(
        "💾 Guardar configuración (JSON)",
        data=preset_json.encode("utf-8"),
        file_name="preset_simulador.json",
        mime="application/json",
    )
