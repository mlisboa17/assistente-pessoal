"""
📱 Módulo de Menus Dinâmicos
Gera menus contextuais com botões para o WhatsApp/Telegram
"""
from typing import List, Dict, Optional
from datetime import datetime


class MenuDinamico:
    """Gerenciador de menus dinâmicos contextuais"""
    
    # Cores do Google Calendar
    CORES_CALENDAR = {
        '1': '🔴 Vermelho (Contas fixas)',
        '2': '🟢 Verde (Entradas)',
        '3': '💙 Azul (Lazer)',
        '4': '💜 Roxo (Investimentos)',
        '5': '🟠 Laranja (Lembretes)',
        '6': '🔵 Azul escuro (Trabalho)',
        '7': '⚫ Cinza (Outros)',
        '8': '🌙 Ciano (Pessoal)',
        '9': '💛 Amarelo (Urgente)',
        '10': '❤️ Vermelho claro (Importante)',
        '11': '🟡 Ouro (Especial)'
    }
    
    @staticmethod
    def menu_principal() -> Dict:
        """Menu principal do bot"""
        return {
            'text': "📱 *Moga Bot - Menu Principal*\n\nO que você gostaria de fazer?",
            'buttons': [
                {'id': 'agenda', 'label': '📅 Minha Agenda'},
                {'id': 'tarefas', 'label': '✅ Tarefas'},
                {'id': 'financas', 'label': '💰 Finanças'},
                {'id': 'ajuda', 'label': '❓ Ajuda'}
            ]
        }
    
    @staticmethod
    def menu_agenda() -> Dict:
        """Menu de agenda com opções de ação"""
        return {
            'text': "📅 *Menu de Agenda*\n\nO que deseja fazer?",
            'buttons': [
                {'id': 'ver_eventos', 'label': '📋 Ver Eventos'},
                {'id': 'add_evento', 'label': '➕ Novo Evento'},
                {'id': 'voltar', 'label': '⬅️ Voltar'}
            ]
        }
    
    @staticmethod
    def menu_finanças() -> Dict:
        """Menu de controle financeiro"""
        return {
            'text': "💰 *Menu de Finanças*\n\nEscolha uma opção:",
            'buttons': [
                {'id': 'ver_gastos', 'label': '💸 Ver Gastos'},
                {'id': 'add_gasto', 'label': '➕ Adicionar Gasto'},
                {'id': 'relatorio', 'label': '📊 Relatório'},
                {'id': 'metas', 'label': '🎯 Metas'},
                {'id': 'voltar', 'label': '⬅️ Voltar'}
            ]
        }
    
    @staticmethod
    def menu_cores_calendar() -> Dict:
        """Menu para escolher cor do evento no Google Calendar"""
        return {
            'text': "🎨 *Escolha a cor do evento:*\n\n" + "\n".join([f"{k}. {v}" for k, v in MenuDinamico.CORES_CALENDAR.items()]),
            'buttons': [
                {'id': f'cor_{i}', 'label': MenuDinamico.CORES_CALENDAR[str(i)]} 
                for i in range(1, 12)
            ]
        }
    
    @staticmethod
    def menu_confirmacao(titulo: str, descricao: str) -> Dict:
        """Menu de confirmação sim/não"""
        return {
            'text': f"❓ *{titulo}*\n\n{descricao}",
            'buttons': [
                {'id': 'sim', 'label': '✅ Sim'},
                {'id': 'nao', 'label': '❌ Não'}
            ]
        }
    
    @staticmethod
    def menu_recorrencia() -> Dict:
        """Menu para escolher recorrência do evento"""
        return {
            'text': "🔁 *Esse evento é recorrente?*",
            'buttons': [
                {'id': 'diario', 'label': '📆 Diário'},
                {'id': 'semanal', 'label': '📅 Semanal'},
                {'id': 'mensal', 'label': '📋 Mensal'},
                {'id': 'nenhum', 'label': '⏸️ Não recorrente'}
            ]
        }
    
    @staticmethod
    def menu_lembrete() -> Dict:
        """Menu para escolher lembrete do evento"""
        return {
            'text': "🔔 *Quando deseja ser lembrado?*",
            'buttons': [
                {'id': 'lembrete_15', 'label': '⏰ 15 minutos antes'},
                {'id': 'lembrete_30', 'label': '⏰ 30 minutos antes'},
                {'id': 'lembrete_1h', 'label': '⏰ 1 hora antes'},
                {'id': 'lembrete_1d', 'label': '⏰ 1 dia antes'},
                {'id': 'lembrete_nao', 'label': '❌ Sem lembrete'}
            ]
        }
    
    @staticmethod
    def menu_tarefas() -> Dict:
        """Menu de tarefas"""
        return {
            'text': "✅ *Menu de Tarefas*\n\nO que você quer fazer?",
            'buttons': [
                {'id': 'listar_tarefas', 'label': '📋 Minhas Tarefas'},
                {'id': 'add_tarefa', 'label': '➕ Nova Tarefa'},
                {'id': 'concluir_tarefa', 'label': '✔️ Concluir Tarefa'},
                {'id': 'voltar', 'label': '⬅️ Voltar'}
            ]
        }
    
    @staticmethod
    def menu_dicas_calendario() -> Dict:
        """Menu com dicas de uso do Google Calendar para finanças"""
        return {
            'text': """💡 *Dicas para usar Google Calendar em Finanças:*

✅ *Marque vencimentos de contas*
Crie eventos recorrentes para despesas fixas (aluguel, energia, internet)

🎨 *Use cores diferentes*
• 🔴 Vermelho = Contas fixas
• 🟢 Verde = Entradas/Salário
• 💙 Azul = Lazer
• 💜 Roxo = Investimentos

🔔 *Configure lembretes*
Configure 2-3 dias antes do vencimento para evitar atrasos

💳 *Controle de cartão de crédito*
Crie dois eventos: "Fechamento da fatura" e "Vencimento da fatura"

💰 *Agende entradas de dinheiro*
Marque salário, freelances e outras fontes de renda

🎯 *Planeje metas financeiras*
Crie eventos para transferências de poupança ou investimentos

📝 *Use descrições detalhadas*
Anote valores, formas de pagamento e observações

📊 *Revisão mensal*
Crie um evento fixo no último dia do mês: "Revisão financeira"
""",
            'buttons': [
                {'id': 'entendi', 'label': '👍 Entendido'},
                {'id': 'voltar', 'label': '⬅️ Voltar'}
            ]
        }
    
    @staticmethod
    def formatar_menu_com_botoes(menu: Dict) -> str:
        """Formata menu para exibição com botões"""
        return menu['text']


# Singleton
_menu_dinamico: Optional[MenuDinamico] = None

def get_menu_dinamico() -> MenuDinamico:
    """Retorna instância singleton do MenuDinamico"""
    global _menu_dinamico
    if _menu_dinamico is None:
        _menu_dinamico = MenuDinamico()
    return _menu_dinamico
