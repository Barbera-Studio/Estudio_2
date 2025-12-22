import pandas as pd
from prophet import Prophet
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Estilo visual
sns.set(style="whitegrid")
plt.rcParams['font.size'] = 13
plt.rcParams['font.family'] = 'DejaVu Sans'

# -------------------------------
# Cargar datos
# -------------------------------
df_original = pd.read_csv('data/pib_esp.csv')
df_original['date'] = pd.to_datetime(df_original['date'])

# Preparar datos para Prophet
df_base = df_original.rename(columns={'date': 'ds', 'pib_norm_100': 'y'})
df_base = df_base.sort_values('ds')  # Asegurar orden cronológico

# Entrenar modelo base
model_base = Prophet(interval_width=0.85)
model_base.fit(df_base)

# -------------------------------
# Crear fechas futuras hasta 2044
# -------------------------------
future = model_base.make_future_dataframe(periods=20, freq='YS')
forecast_base = model_base.predict(future)

# -------------------------------
# Ajustar predicción base al último valor real
# -------------------------------
ultimo_valor_real = df_base['y'].iloc[-1]
primer_valor_predicho = forecast_base['yhat'].iloc[len(df_base)]
factor_ajuste = ultimo_valor_real / primer_valor_predicho

forecast_base['yhat'] *= factor_ajuste
forecast_base['yhat_lower'] *= factor_ajuste
forecast_base['yhat_upper'] *= factor_ajuste

# -------------------------------
# Determinar inicio de escenarios futuros
# -------------------------------
inicio_escenario = df_base['ds'].max()

# -------------------------------
# Función de curva logística extendida
# -------------------------------
def curva_logistica_extendida(df, inicio, factor_final, años, tipo='recuperacion'):
    df = df.copy()
    fechas = df[df['ds'] >= inicio]['ds']
    x = np.linspace(-6, 6, años)
    if tipo == 'shock':
        curva = 1 - (1 - factor_final) / (1 + np.exp(-x))
    else:
        curva = 1 + (factor_final - 1) / (1 + np.exp(-x))

    for i, fecha in enumerate(fechas[:años]):
        df.loc[df['ds'] == fecha, 'yhat'] *= curva[i]

    factor_final_aplicado = curva[-1]
    for fecha in fechas[años:]:
        df.loc[df['ds'] == fecha, 'yhat'] *= factor_final_aplicado

    return df

# -------------------------------
# Escenarios alternativos
# -------------------------------
forecast_neg = curva_logistica_extendida(forecast_base.copy(), inicio_escenario, 0.85, 6, tipo='shock')
forecast_opt = curva_logistica_extendida(forecast_base.copy(), inicio_escenario, 1.10, 6, tipo='recuperacion')

# -------------------------------
# Visualización
# -------------------------------
plt.figure(figsize=(15, 8))

# Histórico
plt.plot(df_base['ds'], df_base['y'], label='Histórico PIB', color='black', linewidth=2.5)

# Escenario base ajustado
plt.plot(forecast_base['ds'], forecast_base['yhat'], label='Escenario base', color='blue', linewidth=2.2)
plt.fill_between(forecast_base['ds'], forecast_base['yhat_lower'], forecast_base['yhat_upper'],
                 color='green', alpha=0.1, label='Intervalo confianza (85%)')

# Escenarios alternativos
plt.plot(forecast_neg['ds'], forecast_neg['yhat'], label='Shock negativo', color='red', linestyle='--', linewidth=2)
plt.plot(forecast_opt['ds'], forecast_opt['yhat'], label='Recuperación optimista', color='limegreen', linestyle='--', linewidth=2)

# Línea dorada y sombreado desde el último dato real
plt.axvline(inicio_escenario, color='gold', linestyle='--', linewidth=2)
plt.axvspan(inicio_escenario, forecast_base['ds'].max(), color='grey', alpha=0.08)

# Anotación narrativa
plt.annotate('Inicio escenarios futuros',
             xy=(inicio_escenario, forecast_base.loc[forecast_base['ds'] == inicio_escenario, 'yhat'].values[0]),
             xytext=(inicio_escenario + pd.DateOffset(years=2),
                     forecast_base['yhat'].max()*1.05),
             arrowprops=dict(facecolor='gold', arrowstyle="->", lw=1.5),
             fontsize=12, color='gold', fontweight='bold')

# Estética final
plt.title('Escenarios de Predicción del PIB Normalizado en España (2000–2044)',
          fontsize=18, fontweight='bold')
plt.xlabel('Año')
plt.ylabel('PIB normalizado (base 100)')
plt.legend(loc='upper left', fontsize=12, frameon=True, facecolor='white')
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show()


