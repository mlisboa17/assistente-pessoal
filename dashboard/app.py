"""
📊 Dashboard Financeiro - Streamlit
Interface web para visualização de finanças, metas e relatórios
"""
import os
import sys
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Adiciona path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Assistente Pessoal - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


class DashboardData:
    """Gerencia dados para o dashboard"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
    
    def load_transacoes(self) -> list:
        """Carrega transações financeiras"""
        file_path = os.path.join(self.data_dir, "transacoes.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def load_metas(self) -> list:
        """Carrega metas financeiras"""
        file_path = os.path.join(self.data_dir, "metas.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def load_boletos(self) -> list:
        """Carrega boletos"""
        file_path = os.path.join(self.data_dir, "boletos.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def load_tarefas(self) -> list:
        """Carrega tarefas"""
        file_path = os.path.join(self.data_dir, "tarefas.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []


# Inicializa dados
data = DashboardData()


def main():
    """Função principal do dashboard"""
    
    # Header
    st.markdown('<p class="main-header">📊 Assistente Pessoal - Dashboard</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/robot-2.png", width=80)
        st.title("Menu")
        
        pagina = st.radio(
            "Navegação",
            ["🏠 Visão Geral", "💰 Finanças", "🎯 Metas", "📄 Boletos", "✅ Tarefas"]
        )
        
        st.divider()
        
        # Filtros
        st.subheader("⚙️ Filtros")
        periodo = st.selectbox(
            "Período",
            ["Últimos 7 dias", "Últimos 30 dias", "Este mês", "Este ano", "Tudo"]
        )
        
        st.divider()
        st.caption("Assistente Pessoal v1.0")
        st.caption(f"Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Conteúdo principal
    if "Visão Geral" in pagina:
        pagina_visao_geral()
    elif "Finanças" in pagina:
        pagina_financas()
    elif "Metas" in pagina:
        pagina_metas()
    elif "Boletos" in pagina:
        pagina_boletos()
    elif "Tarefas" in pagina:
        pagina_tarefas()


def pagina_visao_geral():
    """Página de visão geral"""
    
    transacoes = data.load_transacoes()
    metas = data.load_metas()
    boletos = data.load_boletos()
    tarefas = data.load_tarefas()
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    # Calcula totais
    total_entradas = sum(t.get('valor', 0) for t in transacoes if t.get('tipo') == 'entrada')
    total_saidas = sum(t.get('valor', 0) for t in transacoes if t.get('tipo') == 'saida')
    saldo = total_entradas - total_saidas
    
    boletos_pendentes = len([b for b in boletos if not b.get('pago', False)])
    tarefas_pendentes = len([t for t in tarefas if t.get('status') != 'concluida'])
    metas_ativas = len([m for m in metas if not m.get('concluida', False)])
    
    with col1:
        st.metric("💵 Saldo", f"R$ {saldo:,.2f}", 
                  delta=f"R$ {total_entradas:,.2f} entradas")
    
    with col2:
        st.metric("📉 Gastos", f"R$ {total_saidas:,.2f}",
                  delta=f"{len([t for t in transacoes if t.get('tipo') == 'saida'])} transações")
    
    with col3:
        st.metric("📄 Boletos", f"{boletos_pendentes} pendentes",
                  delta="A vencer" if boletos_pendentes > 0 else "Tudo em dia")
    
    with col4:
        st.metric("✅ Tarefas", f"{tarefas_pendentes} pendentes",
                  delta=f"{metas_ativas} metas ativas")
    
    st.divider()
    
    # Gráficos principais
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Gastos por Categoria")
        if transacoes:
            df = criar_df_gastos_categoria(transacoes)
            if not df.empty:
                fig = px.pie(df, values='valor', names='categoria', 
                            color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum gasto registrado ainda.")
        else:
            st.info("Nenhuma transação registrada ainda.")
    
    with col2:
        st.subheader("📊 Evolução do Saldo")
        if transacoes:
            df = criar_df_evolucao_saldo(transacoes)
            if not df.empty:
                fig = px.line(df, x='data', y='saldo_acumulado',
                             labels={'data': 'Data', 'saldo_acumulado': 'Saldo (R$)'},
                             color_discrete_sequence=['#1f77b4'])
                fig.update_layout(hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dados insuficientes para o gráfico.")
        else:
            st.info("Nenhuma transação registrada ainda.")
    
    # Próximos vencimentos
    st.divider()
    st.subheader("⚠️ Próximos Vencimentos")
    
    if boletos:
        boletos_pendentes = [b for b in boletos if not b.get('pago', False)]
        if boletos_pendentes:
            df_boletos = pd.DataFrame(boletos_pendentes)
            df_boletos = df_boletos[['beneficiario', 'valor', 'vencimento']].head(5)
            df_boletos.columns = ['Beneficiário', 'Valor (R$)', 'Vencimento']
            st.dataframe(df_boletos, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Nenhum boleto pendente!")
    else:
        st.info("Nenhum boleto cadastrado.")


def pagina_financas():
    """Página de finanças detalhada"""
    
    st.header("💰 Finanças")
    
    transacoes = data.load_transacoes()
    
    if not transacoes:
        st.warning("Nenhuma transação registrada. Use o bot para registrar gastos!")
        return
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Resumo", "📋 Transações", "📈 Gráficos"])
    
    with tab1:
        # Métricas do mês
        col1, col2, col3 = st.columns(3)
        
        hoje = datetime.now()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        gastos_mes = sum(
            t.get('valor', 0) for t in transacoes 
            if t.get('tipo') == 'saida' and is_mes_atual(t.get('data', ''), mes_atual, ano_atual)
        )
        entradas_mes = sum(
            t.get('valor', 0) for t in transacoes 
            if t.get('tipo') == 'entrada' and is_mes_atual(t.get('data', ''), mes_atual, ano_atual)
        )
        
        with col1:
            st.metric("📈 Entradas do Mês", f"R$ {entradas_mes:,.2f}")
        with col2:
            st.metric("📉 Gastos do Mês", f"R$ {gastos_mes:,.2f}")
        with col3:
            st.metric("💵 Balanço", f"R$ {entradas_mes - gastos_mes:,.2f}")
        
        # Gastos por categoria do mês
        st.subheader("📊 Gastos por Categoria (Este Mês)")
        
        gastos_categoria = defaultdict(float)
        for t in transacoes:
            if t.get('tipo') == 'saida' and is_mes_atual(t.get('data', ''), mes_atual, ano_atual):
                cat = t.get('categoria', 'outros').title()
                gastos_categoria[cat] += t.get('valor', 0)
        
        if gastos_categoria:
            df = pd.DataFrame([
                {'Categoria': k, 'Valor': v} 
                for k, v in sorted(gastos_categoria.items(), key=lambda x: x[1], reverse=True)
            ])
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(df, x='Categoria', y='Valor', 
                            color='Valor', color_continuous_scale='Blues')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tab2:
        # Lista de transações
        st.subheader("📋 Histórico de Transações")
        
        df = pd.DataFrame(transacoes)
        if 'data' in df.columns:
            df = df.sort_values('data', ascending=False)
        
        colunas = ['data', 'tipo', 'valor', 'descricao', 'categoria']
        colunas_existentes = [c for c in colunas if c in df.columns]
        
        if colunas_existentes:
            df_display = df[colunas_existentes].head(50)
            df_display.columns = ['Data', 'Tipo', 'Valor', 'Descrição', 'Categoria'][:len(colunas_existentes)]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    with tab3:
        # Gráficos avançados
        st.subheader("📈 Análise Temporal")
        
        df = criar_df_gastos_diarios(transacoes)
        if not df.empty:
            fig = px.bar(df, x='data', y=['entradas', 'saidas'],
                        title="Entradas vs Saídas por Dia",
                        barmode='group',
                        labels={'value': 'Valor (R$)', 'data': 'Data'})
            st.plotly_chart(fig, use_container_width=True)


def pagina_metas():
    """Página de metas financeiras"""
    
    st.header("🎯 Metas Financeiras")
    
    metas = data.load_metas()
    
    if not metas:
        st.info("Nenhuma meta cadastrada. Use `/meta criar [nome] [valor]` no bot!")
        
        # Formulário para criar meta
        st.subheader("➕ Criar Nova Meta")
        with st.form("nova_meta"):
            titulo = st.text_input("Título da Meta")
            valor_alvo = st.number_input("Valor Alvo (R$)", min_value=0.0, step=100.0)
            prazo = st.date_input("Prazo")
            
            if st.form_submit_button("Criar Meta"):
                st.success(f"Meta '{titulo}' criada! Use o bot para gerenciar.")
        return
    
    # Lista de metas
    for meta in metas:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            titulo = meta.get('titulo', 'Meta')
            valor_atual = meta.get('valor_atual', 0)
            valor_alvo = meta.get('valor_alvo', 1)
            progresso = min((valor_atual / valor_alvo) * 100, 100) if valor_alvo > 0 else 0
            concluida = meta.get('concluida', False)
            
            with col1:
                status_emoji = "✅" if concluida else "🎯"
                st.subheader(f"{status_emoji} {titulo}")
                
                st.progress(progresso / 100)
                st.caption(f"R$ {valor_atual:,.2f} / R$ {valor_alvo:,.2f} ({progresso:.1f}%)")
            
            with col2:
                if concluida:
                    st.success("Concluída!")
                else:
                    falta = valor_alvo - valor_atual
                    st.metric("Falta", f"R$ {falta:,.2f}")
            
            st.divider()


def pagina_boletos():
    """Página de boletos"""
    
    st.header("📄 Boletos e Contas")
    
    boletos = data.load_boletos()
    
    if not boletos:
        st.info("Nenhum boleto cadastrado. Envie um PDF de boleto pelo bot!")
        return
    
    # Separa pendentes e pagos
    pendentes = [b for b in boletos if not b.get('pago', False)]
    pagos = [b for b in boletos if b.get('pago', False)]
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    
    total_pendente = sum(b.get('valor', 0) for b in pendentes)
    
    with col1:
        st.metric("📋 Pendentes", len(pendentes))
    with col2:
        st.metric("💰 Total a Pagar", f"R$ {total_pendente:,.2f}")
    with col3:
        st.metric("✅ Pagos", len(pagos))
    
    # Tabs
    tab1, tab2 = st.tabs(["⏳ Pendentes", "✅ Pagos"])
    
    with tab1:
        if pendentes:
            for boleto in sorted(pendentes, key=lambda x: x.get('vencimento', '')):
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{boleto.get('beneficiario', 'Boleto')}**")
                        st.caption(f"📅 Vencimento: {boleto.get('vencimento', 'N/A')}")
                    
                    with col2:
                        st.metric("", f"R$ {boleto.get('valor', 0):,.2f}")
                    
                    with col3:
                        venc = boleto.get('vencimento', '')
                        if venc:
                            try:
                                dias = (datetime.fromisoformat(venc).date() - datetime.now().date()).days
                                if dias < 0:
                                    st.error(f"⚠️ Vencido há {-dias}d")
                                elif dias == 0:
                                    st.warning("🔴 Vence hoje!")
                                elif dias <= 3:
                                    st.warning(f"🟠 {dias}d")
                                else:
                                    st.info(f"🟢 {dias}d")
                            except:
                                pass
                    
                    st.divider()
        else:
            st.success("✅ Nenhum boleto pendente!")
    
    with tab2:
        if pagos:
            df = pd.DataFrame(pagos)
            colunas = ['beneficiario', 'valor', 'vencimento']
            df_display = df[[c for c in colunas if c in df.columns]]
            df_display.columns = ['Beneficiário', 'Valor', 'Vencimento'][:len(df_display.columns)]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum boleto pago registrado.")


def pagina_tarefas():
    """Página de tarefas"""
    
    st.header("✅ Tarefas")
    
    tarefas = data.load_tarefas()
    
    if not tarefas:
        st.info("Nenhuma tarefa cadastrada. Use `/tarefa [descrição]` no bot!")
        return
    
    # Separa por status
    pendentes = [t for t in tarefas if t.get('status') == 'pendente']
    em_andamento = [t for t in tarefas if t.get('status') == 'em_andamento']
    concluidas = [t for t in tarefas if t.get('status') == 'concluida']
    
    # Kanban style
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader(f"📋 Pendentes ({len(pendentes)})")
        for t in pendentes:
            with st.container():
                st.write(f"• {t.get('titulo', 'Tarefa')}")
                prioridade = t.get('prioridade', 'media')
                emoji = "🔴" if prioridade == 'alta' else "🟡" if prioridade == 'media' else "🟢"
                st.caption(f"{emoji} {prioridade.title()}")
    
    with col2:
        st.subheader(f"🔄 Em Andamento ({len(em_andamento)})")
        for t in em_andamento:
            with st.container():
                st.write(f"• {t.get('titulo', 'Tarefa')}")
    
    with col3:
        st.subheader(f"✅ Concluídas ({len(concluidas)})")
        for t in concluidas[-5:]:  # Últimas 5
            with st.container():
                st.write(f"~~{t.get('titulo', 'Tarefa')}~~")


# ========== FUNÇÕES AUXILIARES ==========

def criar_df_gastos_categoria(transacoes: list) -> pd.DataFrame:
    """Cria DataFrame de gastos por categoria"""
    gastos = defaultdict(float)
    for t in transacoes:
        if t.get('tipo') == 'saida':
            cat = t.get('categoria', 'outros').title()
            gastos[cat] += t.get('valor', 0)
    
    if not gastos:
        return pd.DataFrame()
    
    return pd.DataFrame([
        {'categoria': k, 'valor': v} 
        for k, v in gastos.items()
    ])


def criar_df_evolucao_saldo(transacoes: list) -> pd.DataFrame:
    """Cria DataFrame de evolução do saldo"""
    if not transacoes:
        return pd.DataFrame()
    
    # Agrupa por data
    por_data = defaultdict(lambda: {'entradas': 0, 'saidas': 0})
    
    for t in transacoes:
        try:
            data_str = t.get('data', '')[:10]  # YYYY-MM-DD
            valor = t.get('valor', 0)
            if t.get('tipo') == 'entrada':
                por_data[data_str]['entradas'] += valor
            else:
                por_data[data_str]['saidas'] += valor
        except:
            continue
    
    if not por_data:
        return pd.DataFrame()
    
    # Ordena e calcula saldo acumulado
    datas = sorted(por_data.keys())
    saldo_acumulado = 0
    registros = []
    
    for data_str in datas:
        saldo_acumulado += por_data[data_str]['entradas'] - por_data[data_str]['saidas']
        registros.append({
            'data': data_str,
            'saldo_acumulado': saldo_acumulado
        })
    
    return pd.DataFrame(registros)


def criar_df_gastos_diarios(transacoes: list) -> pd.DataFrame:
    """Cria DataFrame de gastos diários"""
    por_data = defaultdict(lambda: {'entradas': 0, 'saidas': 0})
    
    for t in transacoes:
        try:
            data_str = t.get('data', '')[:10]
            valor = t.get('valor', 0)
            if t.get('tipo') == 'entrada':
                por_data[data_str]['entradas'] += valor
            else:
                por_data[data_str]['saidas'] += valor
        except:
            continue
    
    if not por_data:
        return pd.DataFrame()
    
    registros = [
        {'data': k, 'entradas': v['entradas'], 'saidas': v['saidas']}
        for k, v in sorted(por_data.items())
    ]
    
    return pd.DataFrame(registros)


def is_mes_atual(data_str: str, mes: int, ano: int) -> bool:
    """Verifica se a data é do mês/ano especificado"""
    try:
        data = datetime.fromisoformat(data_str)
        return data.month == mes and data.year == ano
    except:
        return False


if __name__ == "__main__":
    main()
