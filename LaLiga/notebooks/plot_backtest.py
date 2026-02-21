import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def plot_season_results(df_bets):
    """
    Genera una cuadrícula de gráficos con la evolución del Bankroll (Profit) 
    para cada temporada presente en el DataFrame de apuestas.
    """
    # Asegurar que está ordenado
    df_bets = df_bets.sort_values('Date').copy()
    
    # Obtener lista de temporadas
    seasons = sorted(df_bets['Season'].unique())
    
    # Configurar el grid (2 columnas)
    n_cols = 2
    n_rows = (len(seasons) + 1) // n_cols + ((len(seasons) + 1) % n_cols > 0)
    
    # Tamaño de la figura dinámico
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
    axes = axes.flatten()
    
    # Colores (Estilo "Moderno")
    color_flat = '#3498db'  # Azul
    color_kelly = '#2ecc71' # Verde
    
    print(f"📊 Generando gráficos para {len(seasons)} temporadas...")

    for i, season in enumerate(seasons):
        ax = axes[i]
        
        # Filtrar datos
        season_data = df_bets[df_bets['Season'] == season].copy()
        
        if season_data.empty:
            ax.set_title(f"Temporada {season} (Sin Datos)")
            continue

        # Calcular acumulados
        season_data['Cum_Flat'] = season_data['Flat_Profit'].cumsum()
        season_data['Cum_Kelly'] = season_data['Kelly_Profit'].cumsum()
        
        # Plot
        ax.plot(season_data['Date'], season_data['Cum_Flat'], 
                label='Flat Stake (1u)', color=color_flat, linewidth=2, alpha=0.9)
        ax.plot(season_data['Date'], season_data['Cum_Kelly'], 
                label='Kelly (1/4)', color=color_kelly, linewidth=2, alpha=0.9)
        
        # Línea de break-even
        ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
        
        # Títulos y Leyenda
        ax.set_title(f'Temporada {season}/{season+1}', fontsize=12, fontweight='bold', color='#2c3e50')
        
        # Métricas In-Plot (Caja de info)
        # ROI Flat
        roi_flat = season_data['Flat_Profit'].sum() / (len(season_data) * season_data['Flat_Stake'].iloc[0])
        profit_kelly = season_data['Kelly_Profit'].sum()
        n_bets = len(season_data)
        
        info_text = (
            f"Bets: {n_bets}\n"
            f"ROI Flat: {roi_flat:+.1%}\n"
            f"P&L Kelly: €{profit_kelly:+.0f}"
        )
        
        ax.text(0.03, 0.95, info_text, transform=ax.transAxes, ha='left', va='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='#bdc3c7'),
                fontsize=9, fontfamily='monospace')
        
        if i == 0: # Leyenda solo en el primero para no saturar
            ax.legend(loc='lower right', frameon=True)
            
        ax.grid(True, alpha=0.15)
        ax.tick_params(axis='x', rotation=45, labelsize=8)

    # Ocultar ejes vacíos
    for j in range(i+1, len(axes)):
        axes[j].axis('off')
        
    plt.tight_layout()
    plt.show()

# --- EJEMPLO DE USO (Si se ejecuta directamente) ---
if __name__ == "__main__":
    # Cargar CSV generado por el notebook si existe
    import os
    CSV_PATH = "backtest_bets_v3.csv" 
    
    if os.path.exists(CSV_PATH):
        print(f"📂 Cargando datos de apuestas desde {CSV_PATH}...")
        try:
            df = pd.read_csv(CSV_PATH)
            # Asegurar tipos
            df['Date'] = pd.to_datetime(df['Date'])
            plot_season_results(df)
        except Exception as e:
            print(f"❌ Error al cargar CSV: {e}")
    else:
        print(f"⚠️ No se encontró {CSV_PATH}. Este script está diseñado para usarse dentro del notebook o con el CSV generado.")
