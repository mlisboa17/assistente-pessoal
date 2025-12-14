"""
📊 Dashboard e Visualizador
Gera gráficos, relatórios visuais e dashboards interativos
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from io import BytesIO
import base64

# Matplotlib para gráficos estáticos
try:
    import matplotlib
    matplotlib.use('Agg')  # Backend não-interativo
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Plotly para gráficos interativos
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Seaborn para gráficos estatísticos
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False


class Visualizer:
    """Gerador de visualizações e gráficos"""
    
    # Paleta de cores do tema
    CORES = {
        'primaria': '#3498db',
        'secundaria': '#2ecc71',
        'alerta': '#f39c12',
        'perigo': '#e74c3c',
        'info': '#9b59b6',
        'neutro': '#95a5a6',
        'fundo': '#ffffff',
        'texto': '#2c3e50'
    }
    
    CORES_CATEGORIAS = [
        '#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6',
        '#1abc9c', '#e67e22', '#34495e', '#16a085', '#d35400'
    ]
    
    def __init__(self, output_dir: str = "data/graficos"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Configura estilo padrão
        if MATPLOTLIB_AVAILABLE:
            plt.style.use('seaborn-v0_8-whitegrid')
            plt.rcParams['figure.figsize'] = (10, 6)
            plt.rcParams['font.size'] = 12
    
    # ========== GRÁFICOS DE FINANÇAS ==========
    
    def grafico_gastos_categoria(self, transacoes: List[Dict], 
                                   titulo: str = "Gastos por Categoria") -> Optional[str]:
        """Gera gráfico de pizza de gastos por categoria"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        # Agrupa por categoria
        por_categoria = {}
        for t in transacoes:
            if t.get('tipo') == 'saida':
                cat = t.get('categoria', 'outros')
                por_categoria[cat] = por_categoria.get(cat, 0) + t.get('valor', 0)
        
        if not por_categoria:
            return None
        
        # Ordena por valor
        categorias = sorted(por_categoria.items(), key=lambda x: x[1], reverse=True)
        labels = [c[0].title() for c in categorias]
        valores = [c[1] for c in categorias]
        
        # Cria gráfico
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Cores
        cores = self.CORES_CATEGORIAS[:len(categorias)]
        
        # Pizza
        wedges, texts, autotexts = ax.pie(
            valores,
            labels=labels,
            autopct='%1.1f%%',
            colors=cores,
            explode=[0.02] * len(categorias),
            shadow=True
        )
        
        # Estilo
        plt.setp(autotexts, size=10, weight="bold")
        ax.set_title(titulo, fontsize=14, fontweight='bold')
        
        # Salva
        filepath = os.path.join(self.output_dir, f"gastos_categoria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    def grafico_evolucao_financeira(self, transacoes: List[Dict],
                                     dias: int = 30) -> Optional[str]:
        """Gera gráfico de linha da evolução financeira"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        # Agrupa por dia
        hoje = datetime.now()
        inicio = hoje - timedelta(days=dias)
        
        saldo_diario = {}
        saldo_atual = 0
        
        for t in sorted(transacoes, key=lambda x: x.get('data', '')):
            try:
                data = datetime.fromisoformat(t.get('data', '').split('T')[0])
                if data < inicio:
                    continue
                
                data_str = data.strftime('%Y-%m-%d')
                
                if t.get('tipo') == 'entrada':
                    saldo_atual += t.get('valor', 0)
                else:
                    saldo_atual -= t.get('valor', 0)
                
                saldo_diario[data_str] = saldo_atual
            except:
                pass
        
        if not saldo_diario:
            return None
        
        # Prepara dados
        datas = sorted(saldo_diario.keys())
        valores = [saldo_diario[d] for d in datas]
        datas_dt = [datetime.strptime(d, '%Y-%m-%d') for d in datas]
        
        # Cria gráfico
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Linha
        ax.plot(datas_dt, valores, marker='o', linewidth=2, 
                color=self.CORES['primaria'], markersize=6)
        
        # Preenche área
        ax.fill_between(datas_dt, valores, alpha=0.3, color=self.CORES['primaria'])
        
        # Linha de zero
        ax.axhline(y=0, color=self.CORES['perigo'], linestyle='--', alpha=0.5)
        
        # Formatação
        ax.set_title("Evolução do Saldo", fontsize=14, fontweight='bold')
        ax.set_xlabel("Data")
        ax.set_ylabel("Saldo (R$)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, dias//10)))
        plt.xticks(rotation=45)
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        # Salva
        filepath = os.path.join(self.output_dir, f"evolucao_financeira_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    def grafico_comparativo_mensal(self, transacoes: List[Dict],
                                    meses: int = 6) -> Optional[str]:
        """Gera gráfico de barras comparando entradas x saídas por mês"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        # Agrupa por mês
        por_mes = {}
        
        for t in transacoes:
            try:
                data = datetime.fromisoformat(t.get('data', '').split('T')[0])
                mes = data.strftime('%Y-%m')
                
                if mes not in por_mes:
                    por_mes[mes] = {'entradas': 0, 'saidas': 0}
                
                if t.get('tipo') == 'entrada':
                    por_mes[mes]['entradas'] += t.get('valor', 0)
                else:
                    por_mes[mes]['saidas'] += t.get('valor', 0)
            except:
                pass
        
        if not por_mes:
            return None
        
        # Últimos N meses
        meses_ordenados = sorted(por_mes.keys())[-meses:]
        entradas = [por_mes[m]['entradas'] for m in meses_ordenados]
        saidas = [por_mes[m]['saidas'] for m in meses_ordenados]
        labels = [datetime.strptime(m, '%Y-%m').strftime('%b/%y') for m in meses_ordenados]
        
        # Cria gráfico
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(labels))
        width = 0.35
        
        # Barras
        bars1 = ax.bar([i - width/2 for i in x], entradas, width, 
                       label='Entradas', color=self.CORES['secundaria'])
        bars2 = ax.bar([i + width/2 for i in x], saidas, width, 
                       label='Saídas', color=self.CORES['perigo'])
        
        # Labels nas barras
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'R${height:,.0f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)
        
        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f'R${height:,.0f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)
        
        # Formatação
        ax.set_title("Comparativo Mensal", fontsize=14, fontweight='bold')
        ax.set_ylabel("Valor (R$)")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Salva
        filepath = os.path.join(self.output_dir, f"comparativo_mensal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    # ========== GRÁFICOS DE VENDAS ==========
    
    def grafico_vendas_diarias(self, vendas: List[Dict], 
                                dias: int = 30) -> Optional[str]:
        """Gráfico de vendas diárias"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        # Agrupa por dia
        por_dia = {}
        for v in vendas:
            data = v.get('data', '')
            if isinstance(data, str):
                data = data.split('T')[0]
            por_dia[data] = por_dia.get(data, 0) + v.get('valor_total', 0)
        
        if not por_dia:
            return None
        
        # Últimos N dias
        datas = sorted(por_dia.keys())[-dias:]
        valores = [por_dia.get(d, 0) for d in datas]
        
        # Cria gráfico
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Barras
        cores = [self.CORES['secundaria'] if v > 0 else self.CORES['neutro'] for v in valores]
        ax.bar(range(len(datas)), valores, color=cores)
        
        # Média
        media = sum(valores) / len(valores) if valores else 0
        ax.axhline(y=media, color=self.CORES['alerta'], linestyle='--', 
                   label=f'Média: R${media:,.2f}')
        
        # Formatação
        ax.set_title("Vendas Diárias", fontsize=14, fontweight='bold')
        ax.set_ylabel("Valor (R$)")
        ax.set_xticks(range(0, len(datas), max(1, len(datas)//10)))
        ax.set_xticklabels([datas[i][-5:] for i in range(0, len(datas), max(1, len(datas)//10))], rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Salva
        filepath = os.path.join(self.output_dir, f"vendas_diarias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    def grafico_produtos_mais_vendidos(self, vendas: List[Dict], 
                                        top_n: int = 10) -> Optional[str]:
        """Gráfico de produtos mais vendidos"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        # Conta produtos
        produtos = {}
        for v in vendas:
            for p in v.get('produtos', []):
                nome = p.get('nome', p.get('descricao', 'Produto'))
                produtos[nome] = produtos.get(nome, 0) + p.get('quantidade', 1)
        
        if not produtos:
            return None
        
        # Top N
        top = sorted(produtos.items(), key=lambda x: x[1], reverse=True)[:top_n]
        nomes = [p[0][:20] for p in top]
        qtds = [p[1] for p in top]
        
        # Cria gráfico
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Barras horizontais
        cores = self.CORES_CATEGORIAS[:len(top)]
        bars = ax.barh(range(len(nomes)), qtds, color=cores)
        
        # Labels
        for bar, qtd in zip(bars, qtds):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{qtd}', va='center', fontsize=10)
        
        # Formatação
        ax.set_title("Produtos Mais Vendidos", fontsize=14, fontweight='bold')
        ax.set_xlabel("Quantidade")
        ax.set_yticks(range(len(nomes)))
        ax.set_yticklabels(nomes)
        ax.invert_yaxis()
        ax.grid(True, alpha=0.3, axis='x')
        
        # Salva
        filepath = os.path.join(self.output_dir, f"produtos_top_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    # ========== GRÁFICOS DE TAREFAS ==========
    
    def grafico_tarefas_status(self, tarefas: List[Dict]) -> Optional[str]:
        """Gráfico de tarefas por status"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        # Conta por status
        status_count = {}
        for t in tarefas:
            status = t.get('status', 'pendente')
            status_count[status] = status_count.get(status, 0) + 1
        
        if not status_count:
            return None
        
        # Cores por status
        cores_status = {
            'pendente': self.CORES['alerta'],
            'em_andamento': self.CORES['primaria'],
            'concluida': self.CORES['secundaria']
        }
        
        labels = [s.replace('_', ' ').title() for s in status_count.keys()]
        valores = list(status_count.values())
        cores = [cores_status.get(s, self.CORES['neutro']) for s in status_count.keys()]
        
        # Cria gráfico
        fig, ax = plt.subplots(figsize=(8, 8))
        
        ax.pie(valores, labels=labels, autopct='%1.1f%%', colors=cores,
               explode=[0.02] * len(valores), shadow=True)
        
        ax.set_title("Tarefas por Status", fontsize=14, fontweight='bold')
        
        # Salva
        filepath = os.path.join(self.output_dir, f"tarefas_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    # ========== DASHBOARD COMPLETO ==========
    
    def gerar_dashboard_financeiro(self, transacoes: List[Dict], 
                                    titulo: str = "Dashboard Financeiro") -> Optional[str]:
        """Gera dashboard completo com múltiplos gráficos"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        fig = plt.figure(figsize=(16, 12))
        fig.suptitle(titulo, fontsize=16, fontweight='bold')
        
        # Layout 2x2
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # 1. Gastos por categoria (pizza)
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_gastos_categoria(ax1, transacoes)
        
        # 2. Evolução do saldo (linha)
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_evolucao_saldo(ax2, transacoes)
        
        # 3. Entradas vs Saídas (barras)
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_entradas_saidas(ax3, transacoes)
        
        # 4. Resumo (texto)
        ax4 = fig.add_subplot(gs[1, 1])
        self._plot_resumo(ax4, transacoes)
        
        # Salva
        filepath = os.path.join(self.output_dir, f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    def _plot_gastos_categoria(self, ax, transacoes):
        """Plota gastos por categoria no eixo"""
        por_categoria = {}
        for t in transacoes:
            if t.get('tipo') == 'saida':
                cat = t.get('categoria', 'outros')
                por_categoria[cat] = por_categoria.get(cat, 0) + t.get('valor', 0)
        
        if por_categoria:
            categorias = sorted(por_categoria.items(), key=lambda x: x[1], reverse=True)[:6]
            labels = [c[0].title() for c in categorias]
            valores = [c[1] for c in categorias]
            cores = self.CORES_CATEGORIAS[:len(categorias)]
            
            ax.pie(valores, labels=labels, autopct='%1.1f%%', colors=cores)
        
        ax.set_title("Gastos por Categoria")
    
    def _plot_evolucao_saldo(self, ax, transacoes):
        """Plota evolução do saldo"""
        saldo_diario = {}
        saldo = 0
        
        for t in sorted(transacoes, key=lambda x: x.get('data', '')):
            try:
                data = t.get('data', '').split('T')[0]
                if t.get('tipo') == 'entrada':
                    saldo += t.get('valor', 0)
                else:
                    saldo -= t.get('valor', 0)
                saldo_diario[data] = saldo
            except:
                pass
        
        if saldo_diario:
            datas = list(saldo_diario.keys())[-30:]
            valores = [saldo_diario[d] for d in datas]
            
            ax.plot(range(len(datas)), valores, marker='o', markersize=4,
                   color=self.CORES['primaria'])
            ax.fill_between(range(len(datas)), valores, alpha=0.3)
            ax.axhline(y=0, color=self.CORES['perigo'], linestyle='--', alpha=0.5)
        
        ax.set_title("Evolução do Saldo (30 dias)")
        ax.set_xlabel("Dias")
        ax.set_ylabel("R$")
    
    def _plot_entradas_saidas(self, ax, transacoes):
        """Plota entradas vs saídas"""
        entradas = sum(t.get('valor', 0) for t in transacoes if t.get('tipo') == 'entrada')
        saidas = sum(t.get('valor', 0) for t in transacoes if t.get('tipo') == 'saida')
        
        categorias = ['Entradas', 'Saídas']
        valores = [entradas, saidas]
        cores = [self.CORES['secundaria'], self.CORES['perigo']]
        
        bars = ax.bar(categorias, valores, color=cores)
        
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'R$ {height:,.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontweight='bold')
        
        ax.set_title("Entradas vs Saídas")
        ax.set_ylabel("R$")
    
    def _plot_resumo(self, ax, transacoes):
        """Plota resumo em texto"""
        ax.axis('off')
        
        entradas = sum(t.get('valor', 0) for t in transacoes if t.get('tipo') == 'entrada')
        saidas = sum(t.get('valor', 0) for t in transacoes if t.get('tipo') == 'saida')
        saldo = entradas - saidas
        qtd = len(transacoes)
        
        texto = f"""
RESUMO FINANCEIRO
═══════════════════════

💰 Entradas:    R$ {entradas:>12,.2f}
💸 Saídas:      R$ {saidas:>12,.2f}
───────────────────────
📊 Saldo:       R$ {saldo:>12,.2f}

📋 Total de transações: {qtd}
📅 Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        
        ax.text(0.1, 0.9, texto, transform=ax.transAxes, fontsize=12,
               verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.set_title("Resumo")
    
    # ========== UTILITÁRIOS ==========
    
    def imagem_para_base64(self, filepath: str) -> Optional[str]:
        """Converte imagem para base64 (útil para enviar por API)"""
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def limpar_graficos_antigos(self, dias: int = 7):
        """Remove gráficos antigos"""
        limite = datetime.now() - timedelta(days=dias)
        
        for arquivo in os.listdir(self.output_dir):
            filepath = os.path.join(self.output_dir, arquivo)
            if os.path.isfile(filepath):
                modificado = datetime.fromtimestamp(os.path.getmtime(filepath))
                if modificado < limite:
                    os.remove(filepath)


# Instância global
_visualizer = None

def get_visualizer() -> Visualizer:
    """Retorna instância singleton do Visualizer"""
    global _visualizer
    if _visualizer is None:
        _visualizer = Visualizer()
    return _visualizer
