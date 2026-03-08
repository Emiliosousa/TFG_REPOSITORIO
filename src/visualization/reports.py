import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns

COLORS = {'green': '#27AE60', 'blue': '#2980B9', 'red': '#E74C3C', 'orange': '#F39C12', 'gray': '#95A5A6'}

class FinancialReporter:
    @staticmethod
    def plot_bankroll_evolution(df_bets: pd.DataFrame, initial_bankroll: float, filepath: str = 'investor_report_charts.png'):
        plt.style.use('ggplot')
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Pickslorax — Auditoría Financiera de Inversión', fontsize=16, fontweight='bold', y=1.01)

        # 1. Bankroll Evolution
        ax1 = axes[0, 0]
        ax1.plot(df_bets.index, df_bets['Flat_Bankroll'], color=COLORS['blue'], linewidth=1.5, label='Flat Staking')
        ax1.plot(df_bets.index, df_bets['Kelly_Bankroll'], color=COLORS['green'], linewidth=1.5, label='Kelly 1/4')
        ax1.axhline(initial_bankroll, color=COLORS['red'], linestyle='--', linewidth=1, label='Break Even')
        ax1.fill_between(df_bets.index, initial_bankroll, df_bets['Flat_Bankroll'], 
                         where=df_bets['Flat_Bankroll'] >= initial_bankroll, alpha=0.15, color=COLORS['green'])
        ax1.fill_between(df_bets.index, initial_bankroll, df_bets['Flat_Bankroll'], 
                         where=df_bets['Flat_Bankroll'] < initial_bankroll, alpha=0.15, color=COLORS['red'])
        ax1.set_title('Evolución Absoluta del Capital (Bankroll)', fontweight='bold')
        ax1.set_xlabel('Nº Apuesta')
        ax1.set_ylabel('Capital Disponible (€)')
        ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'€{x:,.0f}'))
        ax1.legend(fontsize=8)

        # 2. Drawdown
        ax3 = axes[1, 0]
        roll_max_flat = df_bets['Flat_Bankroll'].cummax()
        drawdown_flat = (df_bets['Flat_Bankroll'] - roll_max_flat) / roll_max_flat
        ax3.fill_between(df_bets.index, drawdown_flat * 100, 0, alpha=0.6, color=COLORS['red'])
        ax3.set_title('Curva de Drawdown (Pérdida Máxima Estriada)', fontweight='bold')
        ax3.set_xlabel('Nº Apuesta')
        ax3.set_ylabel('Drawdown (%)')

        # 3. Distribución de EV
        ax4 = axes[1, 1]
        ax4.hist(df_bets['EV'] * 100, bins=30, color=COLORS['blue'], edgecolor='white', alpha=0.8)
        ax4.axvline((df_bets['EV'] * 100).mean(), color=COLORS['orange'], linewidth=2, linestyle='--', label=f'EV medio')
        ax4.set_title('Distribución de Expected Value en Selección', fontweight='bold')
        ax4.set_xlabel('Expected Value (%)')
        ax4.set_ylabel('Frecuencia (Nº Apuestas)')
        ax4.legend(fontsize=9)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
